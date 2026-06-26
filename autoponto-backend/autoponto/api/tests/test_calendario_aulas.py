from datetime import date, datetime, time, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    Aula,
    Campus,
    Curso,
    Disciplina,
    HorarioPadraoUFMA,
    MatriculaTurma,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    RegistroPresenca,
    Sala,
    Turma,
    Usuario,
)


def aware_datetime(value: date, hour: int, minute: int = 0):
    return timezone.make_aware(datetime.combine(value, time(hour, minute)))


class CalendarioAulasTests(APITestCase):
    def setUp(self):
        self.aluno = Usuario.objects.create_user(
            username="aluno",
            password="senha",
            papel=PapelUsuario.ALUNO,
            matricula="2026001",
            nome_completo="Aluno Teste",
        )
        self.professor = Usuario.objects.create_user(
            username="professor",
            password="senha",
            papel=PapelUsuario.PROFESSOR,
            nome_completo="Professor Teste",
        )
        self.admin = Usuario.objects.create_user(
            username="admin",
            password="senha",
            papel=PapelUsuario.ADMINISTRADOR,
            nome_completo="Admin Teste",
        )

        campus = Campus.objects.create(nome="Campus Teste")
        predio = Predio.objects.create(campus=campus, nome="Predio Teste")
        self.sala = Sala.objects.create(predio=predio, nome="Sala 101", codigo="101")
        self.periodo = PeriodoLetivo.objects.create(
            nome="2026.1",
            data_inicio=timezone.localdate() - timedelta(days=30),
            data_fim=timezone.localdate() + timedelta(days=30),
            ativo=True,
        )
        curso = Curso.objects.create(campus=campus, nome="Computacao")
        self.disciplina = Disciplina.objects.create(
            curso=curso,
            codigo="COMP001",
            nome="Sistemas Distribuidos",
        )
        self.horario = HorarioPadraoUFMA.objects.create(
            codigo="2M12",
            dia_semana=HorarioPadraoUFMA.DiaSemana.SEGUNDA,
            horario_inicio=time(8, 0),
            horario_fim=time(10, 0),
        )
        self.turma = self.criar_turma("A", ministrada=True, matriculada=True)

    def criar_turma(self, codigo: str, *, ministrada: bool, matriculada: bool):
        turma = Turma.objects.create(
            periodo_letivo=self.periodo,
            disciplina=self.disciplina,
            codigo=codigo,
        )
        if ministrada:
            turma.professores.add(self.professor)
        if matriculada:
            MatriculaTurma.objects.create(turma=turma, aluno=self.aluno, ativo=True)
        return turma

    def criar_aula(self, turma: Turma, value: date, status_aula: str):
        agora = timezone.now()
        inicio = aware_datetime(value, 8)
        fim = aware_datetime(value, 10)
        extras = {}
        if status_aula == Aula.STATUS_PLANEJADA and inicio <= agora:
            value = timezone.localdate() + timedelta(days=7)
            inicio = aware_datetime(value, 8)
            fim = aware_datetime(value, 10)
        elif status_aula == Aula.STATUS_ABERTA:
            value = timezone.localdate()
            inicio = agora - timedelta(minutes=15)
            fim = agora + timedelta(minutes=45)
        elif status_aula == Aula.STATUS_FECHADA and fim > agora:
            extras = {"fechada_em": agora, "fechada_por": self.professor}
        elif status_aula == Aula.STATUS_CANCELADA:
            extras = {"cancelada_em": agora, "cancelada_por": self.professor}
        return Aula.objects.create(
            turma=turma,
            sala=self.sala,
            horario_padrao=self.horario,
            data=value,
            inicio=inicio,
            fim=fim,
            **extras,
        )

    def get_calendario(self, usuario):
        self.client.force_authenticate(usuario)
        inicio = (timezone.localdate() - timedelta(days=14)).isoformat()
        fim = (timezone.localdate() + timedelta(days=14)).isoformat()
        return self.client.get(f"/api/me/calendario-aulas/?inicio={inicio}&fim={fim}")

    def test_aluno_ve_aulas_matriculadas_com_status_derivado(self):
        hoje = timezone.localdate()
        planejada = self.criar_aula(self.turma, hoje + timedelta(days=7), Aula.STATUS_PLANEJADA)
        aberta = self.criar_aula(self.turma, hoje, Aula.STATUS_ABERTA)
        fechada_ausente = self.criar_aula(self.turma, hoje - timedelta(days=7), Aula.STATUS_FECHADA)
        cancelada = self.criar_aula(self.turma, hoje - timedelta(days=5), Aula.STATUS_CANCELADA)
        fechada_presente = self.criar_aula(self.turma, hoje - timedelta(days=3), Aula.STATUS_FECHADA)
        registro = RegistroPresenca.objects.create(
            aula=fechada_presente,
            aluno=self.aluno,
            status=RegistroPresenca.STATUS_PRESENTE,
        )

        response = self.get_calendario(self.aluno)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["visualizacao"], "ALUNO")
        self.assertEqual(response.data["inicio"], (hoje - timedelta(days=14)).isoformat())
        self.assertEqual(response.data["fim"], (hoje + timedelta(days=14)).isoformat())
        aulas = {item["aula_id"]: item for item in response.data["aulas"]}
        self.assertEqual(
            set(aulas),
            {str(aula.id) for aula in [planejada, aberta, fechada_ausente, cancelada, fechada_presente]},
        )
        self.assertEqual(aulas[str(planejada.id)]["status_aluno"], "PENDENTE")
        self.assertEqual(aulas[str(aberta.id)]["status_aluno"], "PENDENTE")
        self.assertEqual(aulas[str(fechada_ausente.id)]["status_aluno"], RegistroPresenca.STATUS_AUSENTE)
        self.assertEqual(aulas[str(cancelada.id)]["status_aluno"], "NAO_APLICAVEL")
        self.assertEqual(aulas[str(fechada_presente.id)]["status_aluno"], RegistroPresenca.STATUS_PRESENTE)
        self.assertEqual(aulas[str(fechada_presente.id)]["presenca_id"], str(registro.id))
        self.assertEqual(aulas[str(planejada.id)]["disciplina"], "Sistemas Distribuidos")

    def test_aluno_nao_ve_aula_de_turma_sem_matricula(self):
        turma_sem_matricula = self.criar_turma("B", ministrada=True, matriculada=False)
        self.criar_aula(self.turma, date(2026, 6, 1), Aula.STATUS_PLANEJADA)
        aula_sem_matricula = self.criar_aula(turma_sem_matricula, date(2026, 6, 8), Aula.STATUS_PLANEJADA)

        response = self.get_calendario(self.aluno)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        aula_ids = {item["aula_id"] for item in response.data["aulas"]}
        self.assertNotIn(str(aula_sem_matricula.id), aula_ids)

    def test_professor_ve_apenas_aulas_que_ministra(self):
        turma_nao_ministrada = self.criar_turma("B", ministrada=False, matriculada=True)
        aula_ministrada = self.criar_aula(self.turma, date(2026, 6, 1), Aula.STATUS_ABERTA)
        aula_nao_ministrada = self.criar_aula(turma_nao_ministrada, date(2026, 6, 8), Aula.STATUS_ABERTA)

        response = self.get_calendario(self.professor)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["visualizacao"], "PROFESSOR")
        aulas = {item["aula_id"]: item for item in response.data["aulas"]}
        self.assertEqual(set(aulas), {str(aula_ministrada.id)})
        self.assertIsNone(aulas[str(aula_ministrada.id)]["status_aluno"])
        self.assertNotIn(str(aula_nao_ministrada.id), aulas)

    def test_admin_ve_todas_as_aulas_em_visualizacao_professor(self):
        turma_nao_ministrada = self.criar_turma("B", ministrada=False, matriculada=False)
        aula_ministrada = self.criar_aula(self.turma, date(2026, 6, 1), Aula.STATUS_FECHADA)
        aula_nao_ministrada = self.criar_aula(turma_nao_ministrada, date(2026, 6, 8), Aula.STATUS_CANCELADA)

        response = self.get_calendario(self.admin)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["visualizacao"], "PROFESSOR")
        aulas = {item["aula_id"]: item for item in response.data["aulas"]}
        self.assertEqual(set(aulas), {str(aula_ministrada.id), str(aula_nao_ministrada.id)})
        self.assertTrue(all(item["status_aluno"] is None for item in aulas.values()))
