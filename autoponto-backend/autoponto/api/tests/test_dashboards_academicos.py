from datetime import date, datetime, time

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    Aula,
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    EventoReconhecimento,
    HorarioPadraoUFMA,
    MatriculaTurma,
    NoBorda,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    RegistroPresenca,
    Sala,
    TokenNoBorda,
    Turma,
    Usuario,
)


def aware_datetime(value: date, hour: int, minute: int = 0):
    return timezone.make_aware(datetime.combine(value, time(hour, minute)))


class DashboardsAcademicosTests(APITestCase):
    def setUp(self):
        self.aluno = Usuario.objects.create_user(
            username="aluno",
            password="senha",
            papel=PapelUsuario.ALUNO,
            matricula="2026001",
            nome_completo="Aluno Teste",
        )
        self.outro_aluno = Usuario.objects.create_user(
            username="outro-aluno",
            password="senha",
            papel=PapelUsuario.ALUNO,
            matricula="2026002",
            nome_completo="Outro Aluno",
        )
        self.professor = Usuario.objects.create_user(
            username="professor",
            password="senha",
            papel=PapelUsuario.PROFESSOR,
            nome_completo="Professor Teste",
        )
        self.outro_professor = Usuario.objects.create_user(
            username="outro-professor",
            password="senha",
            papel=PapelUsuario.PROFESSOR,
            nome_completo="Outro Professor",
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
            data_inicio=date(2026, 6, 1),
            data_fim=date(2026, 6, 30),
            ativo=True,
        )
        self.outro_periodo = PeriodoLetivo.objects.create(
            nome="2026.2",
            data_inicio=date(2026, 7, 1),
            data_fim=date(2026, 7, 31),
            ativo=True,
        )
        curso = Curso.objects.create(campus=campus, nome="Computacao")
        self.disciplina = Disciplina.objects.create(
            curso=curso,
            codigo="COMP001",
            nome="Sistemas Distribuidos",
        )
        self.outra_disciplina = Disciplina.objects.create(
            curso=curso,
            codigo="COMP002",
            nome="Redes",
        )
        self.turma = self.criar_turma("A", self.periodo, self.disciplina, self.professor)
        self.outra_turma = self.criar_turma("B", self.periodo, self.outra_disciplina, self.outro_professor)
        MatriculaTurma.objects.create(turma=self.turma, aluno=self.aluno, ativo=True)
        MatriculaTurma.objects.create(turma=self.turma, aluno=self.outro_aluno, ativo=True)
        MatriculaTurma.objects.create(turma=self.outra_turma, aluno=self.aluno, ativo=True)

    def criar_turma(self, codigo, periodo, disciplina, professor):
        turma = Turma.objects.create(
            periodo_letivo=periodo,
            disciplina=disciplina,
            codigo=codigo,
        )
        turma.professores.add(professor)
        return turma

    def criar_aula(self, turma, value, status_aula, hour=8):
        dia_semana = value.weekday() + 2
        horario, _ = HorarioPadraoUFMA.objects.get_or_create(
            codigo=f"{dia_semana}M12",
            defaults={
                "dia_semana": dia_semana,
                "horario_inicio": time(hour, 0),
                "horario_fim": time(hour + 2, 0),
            },
        )
        return Aula.objects.create(
            turma=turma,
            sala=self.sala,
            horario_padrao=horario,
            data=value,
            inicio=aware_datetime(value, hour),
            fim=aware_datetime(value, hour + 2),
            status=status_aula,
        )

    def autenticar(self, usuario):
        self.client.force_authenticate(usuario)

    def test_status_de_presenca_tem_apenas_presente_e_ausente(self):
        self.assertEqual(
            RegistroPresenca.STATUS_CHOICES,
            (
                (RegistroPresenca.STATUS_PRESENTE, "Presente"),
                (RegistroPresenca.STATUS_AUSENTE, "Ausente"),
            ),
        )
        self.assertFalse(hasattr(RegistroPresenca, "STATUS_ATRASO"))
        self.assertFalse(hasattr(RegistroPresenca, "STATUS_JUSTIFICADA"))

    def test_dashboard_aluno_mostra_aulas_frequencia_e_ultimas_presencas(self):
        hoje = timezone.localdate()
        aula_hoje = self.criar_aula(self.turma, hoje, Aula.STATUS_ABERTA)
        fechada_presente = self.criar_aula(self.turma, date(2026, 6, 8), Aula.STATUS_FECHADA)
        fechada_ausente = self.criar_aula(self.turma, date(2026, 6, 15), Aula.STATUS_FECHADA)
        aula_outra_turma = self.criar_aula(self.outra_turma, date(2026, 6, 22), Aula.STATUS_FECHADA)
        RegistroPresenca.objects.create(
            aula=fechada_presente,
            aluno=self.aluno,
            status=RegistroPresenca.STATUS_PRESENTE,
        )
        RegistroPresenca.objects.create(
            aula=aula_outra_turma,
            aluno=self.aluno,
            status=RegistroPresenca.STATUS_PRESENTE,
        )

        self.autenticar(self.aluno)
        response = self.client.get("/api/me/dashboard-aluno/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["resumo"]["total_fechadas"], 3)
        self.assertEqual(response.data["resumo"]["presentes"], 2)
        self.assertEqual(response.data["resumo"]["ausentes"], 1)
        self.assertEqual(response.data["resumo"]["pendentes"], 1)
        self.assertEqual(response.data["aulas_hoje"][0]["aula_id"], str(aula_hoje.id))
        por_turma = {item["turma_id"]: item for item in response.data["frequencia_por_turma"]}
        self.assertEqual(por_turma[str(self.turma.id)]["faltas"], 1)
        self.assertTrue(all(item["status"] in {"PRESENTE", "AUSENTE", "PENDENTE"} for item in response.data["ultimas_presencas"]))

    def test_dashboard_professor_e_admin_respeitam_permissoes(self):
        aula_ministrada = self.criar_aula(self.turma, timezone.localdate(), Aula.STATUS_ABERTA)
        self.criar_aula(self.outra_turma, timezone.localdate(), Aula.STATUS_ABERTA)

        self.autenticar(self.professor)
        response = self.client.get("/api/professor/dashboard/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["aulas_hoje"][0]["aula_id"], str(aula_ministrada.id))
        self.assertEqual(response.data["totais"]["chamadas_abertas"], 1)
        self.assertEqual(response.data["totais"]["turmas_ministradas"], 1)
        self.assertEqual({item["turma_id"] for item in response.data["turmas"]}, {str(self.turma.id)})

        self.autenticar(self.admin)
        admin_response = self.client.get("/api/professor/dashboard/")
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_response.data["totais"]["turmas_ministradas"], 2)

    def test_frequencia_aluno_filtra_por_periodo_letivo(self):
        aula_presente = self.criar_aula(self.turma, date(2026, 6, 8), Aula.STATUS_FECHADA)
        aula_ausente = self.criar_aula(self.turma, date(2026, 6, 15), Aula.STATUS_FECHADA)
        turma_outro_periodo = self.criar_turma("C", self.outro_periodo, self.disciplina, self.professor)
        MatriculaTurma.objects.create(turma=turma_outro_periodo, aluno=self.aluno, ativo=True)
        self.criar_aula(turma_outro_periodo, date(2026, 7, 6), Aula.STATUS_FECHADA)
        RegistroPresenca.objects.create(aula=aula_presente, aluno=self.aluno)

        self.autenticar(self.aluno)
        response = self.client.get(f"/api/me/frequencia/?periodo_letivo={self.periodo.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["periodo_letivo_id"], str(self.periodo.id))
        self.assertEqual(response.data["resumo"]["total_aulas_fechadas"], 2)
        self.assertEqual(response.data["resumo"]["presencas"], 1)
        self.assertEqual(response.data["resumo"]["faltas"], 1)
        self.assertEqual(response.data["turmas"][0]["percentual"], 50.0)

    def test_frequencia_turma_conta_falta_sem_registro(self):
        aula = self.criar_aula(self.turma, date(2026, 6, 8), Aula.STATUS_FECHADA)
        RegistroPresenca.objects.create(aula=aula, aluno=self.aluno)

        self.autenticar(self.professor)
        response = self.client.get(f"/api/professor/turmas/{self.turma.id}/frequencia/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alunos = {item["aluno_id"]: item for item in response.data["alunos"]}
        self.assertEqual(alunos[str(self.aluno.id)]["faltas"], 0)
        self.assertEqual(alunos[str(self.outro_aluno.id)]["faltas"], 1)
        self.assertEqual(response.data["resumo"]["faltas"], 1)

    def test_detalhe_turma_sem_aula_e_com_aula_eventos_filtrados(self):
        aula = self.criar_aula(self.turma, date(2026, 6, 8), Aula.STATUS_ABERTA)
        outra_aula = self.criar_aula(self.turma, date(2026, 6, 15), Aula.STATUS_ABERTA)
        self.criar_aula(self.turma, timezone.localdate(), Aula.STATUS_PLANEJADA)
        no = NoBorda.objects.create(codigo="NO-1", nome="No 1")
        dispositivo = DispositivoEsp32.objects.create(no=no, sala=self.sala, codigo="ESP-1", nome="ESP 1")
        EventoReconhecimento.objects.create(
            dispositivo=dispositivo,
            aula=aula,
            aluno_candidato=self.aluno,
            confianca="0.9500",
            reconhecido=True,
            ocorrido_em=aware_datetime(date(2026, 6, 8), 8, 30),
        )
        EventoReconhecimento.objects.create(
            dispositivo=dispositivo,
            aula=outra_aula,
            aluno_candidato=self.outro_aluno,
            confianca="0.9100",
            reconhecido=True,
            ocorrido_em=aware_datetime(date(2026, 6, 15), 8, 30),
        )

        self.autenticar(self.professor)
        turma_response = self.client.get(f"/api/turmas/{self.turma.id}/aula/")
        aula_response = self.client.get(f"/api/turmas/{self.turma.id}/aula/{aula.id}/")

        self.assertEqual(turma_response.status_code, status.HTTP_200_OK)
        self.assertIsNone(turma_response.data["aula"])
        self.assertEqual(turma_response.data["turma"]["total_alunos"], 2)
        self.assertGreaterEqual(len(turma_response.data["proximas_aulas"]), 1)
        self.assertEqual(aula_response.status_code, status.HTTP_200_OK)
        self.assertEqual(aula_response.data["aula"]["aula_id"], str(aula.id))
        self.assertEqual(len(aula_response.data["alunos"]), 2)
        self.assertEqual(aula_response.data["alunos"][0]["status"], "PENDENTE")
        self.assertEqual(len(aula_response.data["eventos_reconhecimento"]), 1)
        self.assertEqual(aula_response.data["eventos_reconhecimento"][0]["aluno_id"], str(self.aluno.id))

    def test_aluno_nao_acessa_turma_sem_matricula(self):
        turma_sem_matricula = self.criar_turma("D", self.periodo, self.disciplina, self.professor)
        self.autenticar(self.aluno)
        response = self.client.get(f"/api/turmas/{turma_sem_matricula.id}/aula/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_abrir_chamada_manual_e_fechar_apenas_aberta(self):
        planejada = self.criar_aula(self.turma, date(2026, 6, 8), Aula.STATUS_PLANEJADA)
        fechada = self.criar_aula(self.turma, date(2026, 6, 15), Aula.STATUS_FECHADA)

        self.autenticar(self.professor)
        abrir_response = self.client.post(f"/api/aulas/{planejada.id}/abrir-chamada/")
        planejada.refresh_from_db()
        fechar_planejada_response = self.client.post(f"/api/aulas/{fechada.id}/fechar-chamada/")
        fechar_aberta_response = self.client.post(f"/api/aulas/{planejada.id}/fechar-chamada/")

        self.assertEqual(abrir_response.status_code, status.HTTP_200_OK)
        self.assertEqual(planejada.status, Aula.STATUS_ABERTA)
        self.assertEqual(fechar_planejada_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(fechar_aberta_response.status_code, status.HTTP_200_OK)
        planejada.refresh_from_db()
        self.assertEqual(planejada.status, Aula.STATUS_FECHADA)

    def test_edge_node_continua_abrindo_chamada_automaticamente(self):
        aula = self.criar_aula(self.turma, date(2026, 6, 8), Aula.STATUS_PLANEJADA)
        no = NoBorda.objects.create(codigo="NO-EDGE", nome="No Edge")
        _, token = TokenNoBorda.emitir_token(no, nome="teste")
        dispositivo = DispositivoEsp32.objects.create(no=no, sala=self.sala, codigo="ESP-EDGE", nome="ESP Edge")

        response = self.client.post(
            "/api/edge/attendance/",
            {
                "node_id": no.codigo,
                "eventos": [
                    {
                        "id": "evt-1",
                        "dispositivo_id": str(dispositivo.id),
                        "aula_id": str(aula.id),
                        "aluno_id": str(self.aluno.id),
                        "reconhecido_em": aware_datetime(date(2026, 6, 8), 8, 30).isoformat(),
                        "score": 0.95,
                    }
                ],
            },
            format="json",
            HTTP_X_NODE_TOKEN=token,
        )

        aula.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(aula.status, Aula.STATUS_ABERTA)

    def test_emitir_token_substitui_visualizacao_unica_antiga(self):
        no = NoBorda.objects.create(codigo="NO-TOKEN", nome="No Token")
        token_antigo, _ = TokenNoBorda.emitir_token(no, nome="visualizacao-unica")
        token_integracao, _ = TokenNoBorda.emitir_token(no, nome="integracao")

        self.autenticar(self.admin)
        response = self.client.post(
            f"/api/nos-borda/{no.id}/emitir-token/",
            {"nome": "visualizacao-unica"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(TokenNoBorda.objects.filter(id=token_antigo.id).exists())
        self.assertTrue(TokenNoBorda.objects.filter(id=token_integracao.id).exists())
        self.assertEqual(TokenNoBorda.objects.filter(no=no, nome="visualizacao-unica", ativo=True).count(), 1)
        self.assertEqual(TokenNoBorda.objects.get(no=no, nome="visualizacao-unica").prefixo_token, response.data["prefixo_token"])
