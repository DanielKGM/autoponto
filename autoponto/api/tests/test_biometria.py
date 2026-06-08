from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from api.models import EmbeddingFacial
from .helpers import criar_contexto_academico


class MatriculaBiometricaTests(APITestCase):
    def setUp(self):
        self.contexto = criar_contexto_academico()
        resposta = self.client.post(
            "/api/auth/token/",
            {"username": "admin", "password": "password123"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {resposta.data['access']}")

    @patch("api.services.biometria.GeradorEmbeddingVisao")
    def test_matricula_gera_embedding_sface_e_descarta_frames(self, gerador_cls):
        gerador = gerador_cls.return_value
        gerador.gerar_embedding.return_value = ([0.1, 0.2, 0.3, 0.4], {"quantidade_faces": 2, "modelo": "sface-v1"})

        resposta = self.client.post(
            "/api/perfis-biometricos/matricular/",
            {
                "aluno_id": str(self.contexto["aluno"].id),
                "capturas": ["ZmFrZS1qcGVnLTE=", "ZmFrZS1qcGVnLTI="],
                "versao_modelo": "sface-v1",
                "pontuacao_qualidade": 0.98,
                "metadados_origem": {"origem": "admin-console"},
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        gerador.gerar_embedding.assert_called_once_with(["ZmFrZS1qcGVnLTE=", "ZmFrZS1qcGVnLTI="])
        embedding = EmbeddingFacial.objects.get()
        self.assertEqual(embedding.vetor, [0.1, 0.2, 0.3, 0.4])
        self.assertEqual(embedding.metadados_origem["origem"], "admin-console")
        self.assertEqual(embedding.metadados_origem["quantidade_faces"], 2)
        self.assertNotIn("capturas", embedding.metadados_origem)
        self.assertNotIn("frames", embedding.metadados_origem)
