from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import DispositivoEsp32, HorarioAula, MatriculaTurma, RegistroPresenca
from api.services import matricular_biometria_aluno, obter_ou_criar_aula
from .helpers import criar_contexto_academico


class ModeloDominioTests(TestCase):
    def setUp(self):
        self.contexto = criar_contexto_academico()

    def test_matricula_deve_ser_unica_por_aluno_e_turma(self):
        with self.assertRaises(ValidationError):
            MatriculaTurma.objects.create(
                turma=self.contexto["turma"],
                aluno=self.contexto["aluno"],
            )

    def test_horario_impede_choque_de_sala_no_mesmo_periodo(self):
        outra_turma = self.contexto["turma"].__class__.objects.create(
            periodo_letivo=self.contexto["periodo"],
            disciplina=self.contexto["disciplina"],
            codigo="B",
            nome="Turma B",
        )
        with self.assertRaises(ValidationError):
            HorarioAula.objects.create(
                turma=outra_turma,
                sala=self.contexto["sala"],
                dia_semana=self.contexto["horario"].dia_semana,
                horario_inicio=self.contexto["horario"].horario_inicio,
                horario_fim=self.contexto["horario"].horario_fim,
            )

    def test_apenas_um_dispositivo_ativo_por_sala(self):
        with self.assertRaises(ValidationError):
            DispositivoEsp32.objects.create(
                codigo="ESP32-LAB101-B",
                nome="ESP32 Reserva",
                sala=self.contexto["sala"],
                ativo=True,
            )

    def test_presenca_deve_ser_unica_por_aluno_e_aula(self):
        aula, _ = obter_ou_criar_aula(self.contexto["horario"], self.contexto["data_aula"])
        RegistroPresenca.objects.create(aula=aula, aluno=self.contexto["aluno"])
        with self.assertRaises(ValidationError):
            RegistroPresenca.objects.create(aula=aula, aluno=self.contexto["aluno"])

    @patch("api.services.biometria.GeradorEmbeddingVisao")
    def test_matricula_biometrica_mantem_um_embedding_ativo(self, gerador_cls):
        gerador_cls.return_value.gerar_embedding.side_effect = [
            ([0.1, 0.2], {"quantidade_faces": 1}),
            ([0.3, 0.4], {"quantidade_faces": 1}),
        ]
        perfil, primeiro_embedding = matricular_biometria_aluno(
            aluno=self.contexto["aluno"],
            capturas=["captura-a"],
            versao_modelo="sface-v1",
        )
        _, segundo_embedding = matricular_biometria_aluno(
            aluno=self.contexto["aluno"],
            capturas=["captura-b"],
            versao_modelo="sface-v2",
        )

        primeiro_embedding.refresh_from_db()
        segundo_embedding.refresh_from_db()
        perfil.refresh_from_db()

        self.assertEqual(perfil.status, "ATIVO")
        self.assertFalse(primeiro_embedding.ativo)
        self.assertTrue(segundo_embedding.ativo)
