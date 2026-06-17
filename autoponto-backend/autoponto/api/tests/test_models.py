from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.models import (
    DispositivoEsp32,
    HorarioAula,
    HorarioPadraoUFMA,
    MatriculaTurma,
    PapelUsuario,
    RegistroPresenca,
    Usuario,
)
from api.services import matricular_biometria_aluno, obter_ou_criar_aula
from .helpers import criar_contexto_academico


class ModeloDominioTests(TestCase):
    def setUp(self):
        self.contexto = criar_contexto_academico()


    def test_usuario_pode_ser_criado_sem_email(self):
        usuario = Usuario.objects.create_user(
            username="aluno-sem-email",
            password="password123",
            papel=PapelUsuario.ALUNO,
            nome_completo="Aluno Sem Email",
        )

        self.assertEqual(usuario.email, "")

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
                horario_padrao=self.contexto["horario_padrao"],
            )

    def test_horario_padrao_ufma_valida_codigo_dia_e_intervalo(self):
        with self.assertRaises(ValidationError):
            HorarioPadraoUFMA.objects.create(
                codigo="3M12",
                dia_semana=HorarioPadraoUFMA.DiaSemana.SEGUNDA,
                horario_inicio=self.contexto["horario_padrao"].horario_inicio,
                horario_fim=self.contexto["horario_padrao"].horario_fim,
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

    def test_aula_salva_snapshot_da_duracao_do_horario_ufma(self):
        horario = self.contexto["horario"]

        aula, _ = obter_ou_criar_aula(horario, self.contexto["data_aula"])

        self.assertEqual(aula.inicio.hour, 8)
        self.assertEqual(aula.inicio.minute, 0)
        self.assertEqual(aula.fim.hour, 9)
        self.assertEqual(aula.fim.minute, 40)

    def test_aula_preserva_inicio_e_fim_se_horario_padrao_mudar_depois(self):
        horario = self.contexto["horario"]
        aula, _ = obter_ou_criar_aula(horario, self.contexto["data_aula"])
        inicio_original = aula.inicio
        fim_original = aula.fim

        padrao = self.contexto["horario_padrao"]
        padrao.horario_inicio = padrao.horario_inicio.replace(hour=10)
        padrao.horario_fim = padrao.horario_fim.replace(hour=11)
        padrao.save(update_fields=["horario_inicio", "horario_fim", "atualizado_em"])

        aula.refresh_from_db()
        self.assertEqual(aula.inicio, inicio_original)
        self.assertEqual(aula.fim, fim_original)

    @patch("api.services.biometria.GeradorEmbeddingVisao")
    def test_matricula_biometrica_mantem_um_embedding_ativo(self, gerador_cls):
        gerador_cls.return_value.gerar_embedding.side_effect = [
            ([0.1, 0.2], {"quantidade_faces": 1}),
            ([0.3, 0.4], {"quantidade_faces": 1}),
        ]
        perfil, primeiro_embedding = matricular_biometria_aluno(
            aluno=self.contexto["aluno"],
            capturas=["Y2FwdHVyYS1h"],
            versao_modelo="sface-v1",
        )
        _, segundo_embedding = matricular_biometria_aluno(
            aluno=self.contexto["aluno"],
            capturas=["Y2FwdHVyYS1i"],
            versao_modelo="sface-v2",
        )

        primeiro_embedding.refresh_from_db()
        segundo_embedding.refresh_from_db()
        perfil.refresh_from_db()

        self.assertEqual(perfil.status, "ATIVO")
        self.assertFalse(primeiro_embedding.ativo)
        self.assertTrue(segundo_embedding.ativo)
