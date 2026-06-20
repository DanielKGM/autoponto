from unittest.mock import patch

from django.test import TestCase

from api.models import EmbeddingFacial, PapelUsuario, Usuario
from api.services.biometria import matricular_biometria_aluno


class BiometriaTests(TestCase):
    def test_matricula_biometrica_atualiza_unico_embedding_do_aluno(self):
        aluno = Usuario.objects.create_user(
            username="aluno",
            password="senha",
            papel=PapelUsuario.ALUNO,
            matricula="20260001",
        )
        embedding_antigo = EmbeddingFacial.objects.create(
            aluno=aluno,
            versao_modelo="sface-antigo",
            vetor=[0.1, 0.2],
            status="ATIVO",
            ativo=True,
        )

        with patch(
            "api.services.biometria._gerar_vetor_embedding",
            return_value=([0.3, 0.4], {"modelo": "sface"}),
        ):
            embedding = matricular_biometria_aluno(
                aluno=aluno,
                capturas=["ZmFrZQ=="],
                versao_modelo="sface",
            )

        self.assertEqual(EmbeddingFacial.objects.filter(aluno=aluno).count(), 1)
        self.assertEqual(embedding.id, embedding_antigo.id)
        self.assertEqual(embedding.versao_modelo, "sface")
        self.assertEqual(embedding.vetor, [0.3, 0.4])
        self.assertEqual(embedding.status, "ATIVO")
        self.assertTrue(embedding.ativo)
