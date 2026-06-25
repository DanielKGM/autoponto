import base64

from django.test import SimpleTestCase, override_settings

from api.serializers.frontend import MatriculaBiometricaPropriaSerializer


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
