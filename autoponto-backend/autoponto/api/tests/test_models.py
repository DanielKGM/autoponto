from unittest.mock import patch
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from api.models import DispositivoEsp32, HorarioAula, MatriculaTurma, RegistroPresenca
from api.services import matricular_biometria_aluno, obter_ou_criar_aula, recalcular_janelas_aulas_futuras
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

    def test_aula_salva_snapshot_da_janela_de_chamada(self):
        horario = self.contexto["horario"]
        horario.abre_chamada_minutos = 10
        horario.fecha_chamada_minutos = 40
        horario.save(update_fields=["abre_chamada_minutos", "fecha_chamada_minutos", "atualizado_em"])

        aula, _ = obter_ou_criar_aula(horario, self.contexto["data_aula"])

        self.assertEqual(aula.chamada_inicio.minute, 10)
        self.assertEqual(aula.chamada_fim.minute, 40)

    def test_recalculo_de_janela_preserva_aulas_passadas_e_fechadas(self):
        horario = self.contexto["horario"]
        aula_passada, _ = obter_ou_criar_aula(horario, self.contexto["data_aula"])
        data_futura = timezone.localdate()
        deslocamento = (horario.dia_semana - data_futura.weekday()) % 7 or 7
        data_futura = data_futura + timedelta(days=deslocamento)
        aula_futura, _ = obter_ou_criar_aula(horario, data_futura)
        aula_fechada, _ = obter_ou_criar_aula(horario, data_futura + timedelta(days=7))
        aula_fechada.status = aula_fechada.STATUS_FECHADA
        aula_fechada.save(update_fields=["status", "atualizado_em"])
        chamada_passada = aula_passada.chamada_fim
        chamada_fechada = aula_fechada.chamada_fim

        horario.fecha_chamada_minutos = 30
        horario.save(update_fields=["fecha_chamada_minutos", "atualizado_em"])
        atualizadas = recalcular_janelas_aulas_futuras(horario)

        aula_passada.refresh_from_db()
        aula_futura.refresh_from_db()
        aula_fechada.refresh_from_db()
        self.assertEqual(atualizadas, 1)
        self.assertEqual(aula_passada.chamada_fim, chamada_passada)
        self.assertEqual(aula_fechada.chamada_fim, chamada_fechada)
        self.assertEqual((aula_futura.chamada_fim - aula_futura.inicio).total_seconds(), 30 * 60)

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
