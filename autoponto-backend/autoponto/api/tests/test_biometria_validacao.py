import base64
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase, SimpleTestCase, override_settings

from api.models import EmbeddingFacial, PapelUsuario, Usuario
from api.serializers.frontend import MatriculaBiometricaPropriaSerializer
from api.services.biometria import (
    ComparadorEmbeddingSFace,
    matricular_biometria_aluno,
    validar_rosto_unico,
)
from api.services.cache_biometria import limpar_locmem_para_testes, salvar_embedding
from api.services.crypto_biometria import criptografar_vetor
from api.services.errors import ConflictError


FERNET_TEST_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


def payload_imagem(bruto: bytes) -> str:
    return base64.b64encode(bruto).decode("ascii")


class BiometriaValidacaoTests(SimpleTestCase):
    @override_settings(FACE_MAX_CAPTURAS=5, FACE_MAX_IMAGE_BYTES=64)
    def test_aceita_imagem_png_dentro_do_limite(self):
        serializer = MatriculaBiometricaPropriaSerializer(
            data={
                "capturas": [payload_imagem(b"\x89PNG\r\n\x1a\n" + b"0" * 12)],
                "versao_modelo": "sface",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    @override_settings(FACE_MAX_CAPTURAS=5, FACE_MAX_IMAGE_BYTES=16)
    def test_rejeita_imagem_acima_do_limite(self):
        serializer = MatriculaBiometricaPropriaSerializer(
            data={
                "capturas": [payload_imagem(b"\x89PNG\r\n\x1a\n" + b"0" * 32)],
                "versao_modelo": "sface",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("excede o limite", str(serializer.errors))

    @override_settings(FACE_MAX_CAPTURAS=5, FACE_MAX_IMAGE_BYTES=64)
    def test_rejeita_formato_nao_permitido(self):
        serializer = MatriculaBiometricaPropriaSerializer(
            data={
                "capturas": [payload_imagem(b"GIF89a" + b"0" * 12)],
                "versao_modelo": "sface",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("JPEG, PNG ou WebP", str(serializer.errors))

    @override_settings(FACE_RECOG_MODEL_PATH="modelo.onnx")
    @patch("api.services.biometria._resolver_caminho_modelo", return_value="modelo.onnx")
    def test_comparador_sface_usa_reconhecedor_match(self, _resolver):
        class FakeArray(list):
            def reshape(self, *_args):
                return self

        reconhecedor = SimpleNamespace(match=Mock(return_value=0.99))
        fake_np = SimpleNamespace(
            asarray=Mock(side_effect=lambda vetor, dtype: FakeArray(vetor))
        )
        fake_cv2 = SimpleNamespace(
            FaceRecognizerSF=SimpleNamespace(
                create=Mock(return_value=reconhecedor)
            ),
            FaceRecognizerSF_FR_COSINE=123,
        )
        with patch.dict("sys.modules", {"cv2": fake_cv2, "numpy": fake_np}):
            comparador = ComparadorEmbeddingSFace()
            similaridade = comparador.similaridade([1.0, 0.0], [1.0, 0.0])

        self.assertEqual(similaridade, 0.99)
        fake_cv2.FaceRecognizerSF.create.assert_called_once_with("modelo.onnx", "")
        fake_np.asarray.assert_any_call([1.0, 0.0], dtype="float32")
        reconhecedor.match.assert_called_once()
        self.assertEqual(reconhecedor.match.call_args.args[2], 123)


@override_settings(
    FACE_EMBEDDING_ENCRYPTION_KEY=FERNET_TEST_KEY,
    FACE_EMBEDDING_CACHE_URL="locmem://",
    FACE_DUPLICATE_THRESHOLD=0.85,
)
class BiometriaCriptografiaCacheTests(TestCase):
    def setUp(self):
        limpar_locmem_para_testes()
        self.aluno = Usuario.objects.create_user(
            username="aluno-bio",
            password="senha",
            papel=PapelUsuario.ALUNO,
            matricula="2026001",
        )
        self.outro_aluno = Usuario.objects.create_user(
            username="outro-bio",
            password="senha",
            papel=PapelUsuario.ALUNO,
            matricula="2026002",
        )

    def tearDown(self):
        limpar_locmem_para_testes()

    @patch("api.services.biometria._gerar_vetor_embedding", return_value=([1.0, 0.0], {"modelo": "sface"}))
    def test_matricula_salva_vetor_criptografado(self, _gerar):
        embedding = matricular_biometria_aluno(
            aluno=self.aluno,
            capturas=["captura-ja-validada"],
            versao_modelo="sface",
        )

        embedding.refresh_from_db()
        self.assertIsInstance(embedding.vetor, str)
        self.assertNotIn("[1.0,0.0]", embedding.vetor)

    @patch("api.services.biometria.ComparadorEmbeddingSFace")
    def test_validacao_global_usa_cache_e_bloqueia_rosto_duplicado(self, comparador_cls):
        comparador_cls.return_value.similaridade.return_value = 1.0
        existente = EmbeddingFacial.objects.create(
            aluno=self.outro_aluno,
            versao_modelo="sface",
            vetor=criptografar_vetor([1.0, 0.0]),
            status=EmbeddingFacial.STATUS_ATIVO,
            ativo=True,
        )
        salvar_embedding(existente)

        with self.assertRaises(ConflictError):
            validar_rosto_unico(aluno=self.aluno, vetor=[1.0, 0.0])

        comparador_cls.return_value.similaridade.assert_called_once()

    @patch("api.services.biometria.ComparadorEmbeddingSFace")
    def test_cache_vazio_reconstroi_do_banco(self, comparador_cls):
        comparador_cls.return_value.similaridade.return_value = 1.0
        EmbeddingFacial.objects.create(
            aluno=self.outro_aluno,
            versao_modelo="sface",
            vetor=criptografar_vetor([1.0, 0.0]),
            status=EmbeddingFacial.STATUS_ATIVO,
            ativo=True,
        )
        limpar_locmem_para_testes()

        with self.assertRaises(ConflictError):
            validar_rosto_unico(aluno=self.aluno, vetor=[1.0, 0.0])
