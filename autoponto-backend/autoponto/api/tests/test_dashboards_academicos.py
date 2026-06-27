from datetime import date, datetime, time, timedelta

from django.test import override_settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    Aula,
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    EmbeddingFacial,
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
from api.selectors.aulas import status_aula
from api.services.aulas import sincronizar_aulas_da_turma
from api.services.crypto_biometria import criptografar_vetor
from api.services.errors import DomainValidationError


FERNET_TEST_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


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

    def criar_aula(self, turma, value, status_desejado, hour=8):
        agora = timezone.now()
        inicio = aware_datetime(value, hour)
        fim = aware_datetime(value, hour + 2)
        extras = {}
        if status_desejado == Aula.STATUS_PLANEJADA and inicio <= agora:
            value = timezone.localdate() + timedelta(days=7)
            inicio = aware_datetime(value, hour)
            fim = aware_datetime(value, hour + 2)
        elif status_desejado == Aula.STATUS_ABERTA:
            value = timezone.localdate()
            inicio = agora - timedelta(minutes=15)
            fim = agora + timedelta(minutes=45)
        elif status_desejado == Aula.STATUS_FECHADA and fim > agora:
            extras = {"fechada_em": agora, "fechada_por": self.professor}
        elif status_desejado == Aula.STATUS_CANCELADA:
            extras = {"cancelada_em": agora, "cancelada_por": self.professor}

        dia_semana = value.weekday() + 2
        horario = HorarioPadraoUFMA.objects.create(
            codigo=f"{dia_semana}M{HorarioPadraoUFMA.objects.count() + 1}",
            dia_semana=dia_semana,
            horario_inicio=inicio.time().replace(second=0, microsecond=0),
            horario_fim=fim.time().replace(second=0, microsecond=0),
        )
        return Aula.objects.create(
            turma=turma,
            sala=self.sala,
            horario_padrao=horario,
            data=value,
            inicio=inicio,
            fim=fim,
            **extras,
        )

    def autenticar(self, usuario):
        self.client.force_authenticate(usuario)

    def proxima_data_com_dia_semana(self, dia_semana):
        hoje = timezone.localdate()
        dias_ate_data = (int(dia_semana) - 2 - hoje.weekday()) % 7
        if dias_ate_data == 0:
            dias_ate_data = 7
        return hoje + timedelta(days=dias_ate_data)

    def data_anterior_com_dia_semana(self, dia_semana):
        hoje = timezone.localdate()
        dias_desde_data = (hoje.weekday() - (int(dia_semana) - 2)) % 7
        if dias_desde_data == 0:
            dias_desde_data = 7
        return hoje - timedelta(days=dias_desde_data)

    def criar_horario_padrao(self, codigo, hour):
        dia_semana = int(codigo[0])
        return HorarioPadraoUFMA.objects.create(
            codigo=codigo,
            dia_semana=dia_semana,
            horario_inicio=time(hour, 0),
            horario_fim=time(hour + 2, 0),
        )

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

    def test_admin_cria_professor_sem_matricula_mas_exige_para_aluno(self):
        self.autenticar(self.admin)

        professor_response = self.client.post(
            "/api/usuarios/",
            {
                "username": "professor-sem-matricula",
                "password": "senha",
                "papel": PapelUsuario.PROFESSOR,
                "nome_completo": "Professor Sem Matricula",
            },
            format="json",
        )
        aluno_response = self.client.post(
            "/api/usuarios/",
            {
                "username": "aluno-sem-matricula",
                "password": "senha",
                "papel": PapelUsuario.ALUNO,
                "nome_completo": "Aluno Sem Matricula",
            },
            format="json",
        )

        self.assertEqual(professor_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(professor_response.data["matricula"], "")
        self.assertEqual(aluno_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("matricula", aluno_response.data)

    def test_turma_retorna_horarios_de_aulas_futuras_nao_canceladas(self):
        hoje = timezone.localdate()
        periodo = PeriodoLetivo.objects.create(
            nome="Periodo horarios response",
            data_inicio=hoje - timedelta(days=7),
            data_fim=hoje + timedelta(days=21),
            ativo=True,
        )
        turma = self.criar_turma("HOR", periodo, self.disciplina, self.professor)
        horario_ativo = self.criar_horario_padrao("2M12", 8)
        horario_cancelado = self.criar_horario_padrao("3M34", 10)
        data_passada = self.data_anterior_com_dia_semana(horario_ativo.dia_semana)
        data_futura_ativa = self.proxima_data_com_dia_semana(horario_ativo.dia_semana)
        data_futura_cancelada = self.proxima_data_com_dia_semana(horario_cancelado.dia_semana)

        Aula.objects.create(
            turma=turma,
            sala=self.sala,
            horario_padrao=horario_ativo,
            data=data_passada,
            inicio=aware_datetime(data_passada, 8),
            fim=aware_datetime(data_passada, 10),
        )
        Aula.objects.create(
            turma=turma,
            sala=self.sala,
            horario_padrao=horario_ativo,
            data=data_futura_ativa,
            inicio=aware_datetime(data_futura_ativa, 8),
            fim=aware_datetime(data_futura_ativa, 10),
        )
        Aula.objects.create(
            turma=turma,
            sala=self.sala,
            horario_padrao=horario_cancelado,
            data=data_futura_cancelada,
            inicio=aware_datetime(data_futura_cancelada, 10),
            fim=aware_datetime(data_futura_cancelada, 12),
            cancelada_em=timezone.now(),
            cancelada_por=self.professor,
        )

        self.autenticar(self.admin)
        response = self.client.get(f"/api/turmas/{turma.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["horarios"],
            [{"sala": str(self.sala.id), "horario_padrao": str(horario_ativo.id)}],
        )

    def test_editar_turma_remove_horario_futuro_e_recusa_turma_ativa_sem_horarios(self):
        hoje = timezone.localdate()
        periodo = PeriodoLetivo.objects.create(
            nome="Periodo horarios edit",
            data_inicio=hoje - timedelta(days=7),
            data_fim=hoje + timedelta(days=21),
            ativo=True,
        )
        turma = self.criar_turma("EDT", periodo, self.disciplina, self.professor)
        horario_mantido = self.criar_horario_padrao("2T12", 14)
        horario_removido = self.criar_horario_padrao("3T34", 16)
        data_mantida = self.proxima_data_com_dia_semana(horario_mantido.dia_semana)
        data_removida = self.proxima_data_com_dia_semana(horario_removido.dia_semana)
        aula_mantida = Aula.objects.create(
            turma=turma,
            sala=self.sala,
            horario_padrao=horario_mantido,
            data=data_mantida,
            inicio=aware_datetime(data_mantida, 14),
            fim=aware_datetime(data_mantida, 16),
        )
        aula_removida = Aula.objects.create(
            turma=turma,
            sala=self.sala,
            horario_padrao=horario_removido,
            data=data_removida,
            inicio=aware_datetime(data_removida, 16),
            fim=aware_datetime(data_removida, 18),
        )

        self.autenticar(self.admin)
        update_response = self.client.patch(
            f"/api/turmas/{turma.id}/",
            {"horarios": [{"sala": str(self.sala.id), "horario_padrao": str(horario_mantido.id)}]},
            format="json",
        )
        empty_response = self.client.patch(
            f"/api/turmas/{turma.id}/",
            {"horarios": []},
            format="json",
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        aula_mantida.refresh_from_db()
        aula_removida.refresh_from_db()
        self.assertEqual(status_aula(aula_mantida), Aula.STATUS_PLANEJADA)
        self.assertEqual(status_aula(aula_removida), Aula.STATUS_CANCELADA)
        self.assertIsNotNone(aula_removida.cancelada_em)
        self.assertEqual(empty_response.status_code, status.HTTP_400_BAD_REQUEST)

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
        no = NoBorda.objects.create(
            codigo="NO-SYNC",
            nome="No Sync",
            ultimo_sync_em=aware_datetime(date(2026, 6, 20), 9),
        )
        DispositivoEsp32.objects.create(no=no, sala=self.sala, codigo="ESP-SYNC", nome="ESP Sync")

        self.autenticar(self.aluno)
        response = self.client.get(f"/api/me/frequencia/?periodo_letivo={self.periodo.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["periodo_letivo_id"], str(self.periodo.id))
        self.assertEqual(response.data["resumo"]["total_aulas_fechadas"], 2)
        self.assertEqual(response.data["resumo"]["presencas"], 1)
        self.assertEqual(response.data["resumo"]["faltas"], 1)
        self.assertEqual(response.data["turmas"][0]["percentual"], 50.0)
        self.assertEqual(response.data["turmas"][0]["no_borda_codigo"], "NO-SYNC")
        self.assertEqual(
            parse_datetime(response.data["turmas"][0]["ultimo_sync_no_borda"]),
            aware_datetime(date(2026, 6, 20), 9),
        )

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
        agora = timezone.localtime()
        data_atual = agora.date()
        dia_semana = data_atual.weekday() + 2
        horario_abertura = HorarioPadraoUFMA.objects.create(
            codigo=f"{dia_semana}M12",
            dia_semana=dia_semana,
            horario_inicio=(agora - timedelta(minutes=15)).time(),
            horario_fim=(agora + timedelta(minutes=45)).time(),
        )
        horario_fechada = HorarioPadraoUFMA.objects.create(
            codigo=f"{dia_semana}M34",
            dia_semana=dia_semana,
            horario_inicio=(agora - timedelta(minutes=20)).time(),
            horario_fim=(agora + timedelta(minutes=40)).time(),
        )
        planejada = Aula.objects.create(
            turma=self.turma,
            sala=self.sala,
            horario_padrao=horario_abertura,
            data=data_atual,
            inicio=agora - timedelta(minutes=15),
            fim=agora + timedelta(minutes=45),
        )
        fechada = Aula.objects.create(
            turma=self.turma,
            sala=self.sala,
            horario_padrao=horario_fechada,
            data=data_atual,
            inicio=agora - timedelta(minutes=20),
            fim=agora + timedelta(minutes=40),
            fechada_em=agora - timedelta(minutes=5),
            fechada_por=self.professor,
        )

        self.autenticar(self.professor)
        abrir_response = self.client.post(f"/api/aulas/{planejada.id}/abrir-chamada/")
        planejada.refresh_from_db()
        fechar_planejada_response = self.client.post(f"/api/aulas/{fechada.id}/fechar-chamada/")
        fechar_aberta_response = self.client.post(f"/api/aulas/{planejada.id}/fechar-chamada/")

        self.assertEqual(abrir_response.status_code, status.HTTP_200_OK)
        self.assertEqual(status_aula(planejada), Aula.STATUS_ABERTA)
        self.assertEqual(fechar_planejada_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(fechar_aberta_response.status_code, status.HTTP_200_OK)
        planejada.refresh_from_db()
        self.assertEqual(status_aula(planejada), Aula.STATUS_FECHADA)

    def test_abrir_chamada_manual_bloqueia_aula_fora_da_janela(self):
        futura = self.criar_aula(self.turma, timezone.localdate() + timedelta(days=1), Aula.STATUS_PLANEJADA)
        passada = self.criar_aula(self.turma, timezone.localdate() - timedelta(days=1), Aula.STATUS_PLANEJADA)

        self.autenticar(self.professor)
        futura_response = self.client.post(f"/api/aulas/{futura.id}/abrir-chamada/")
        passada_response = self.client.post(f"/api/aulas/{passada.id}/abrir-chamada/")

        self.assertEqual(futura_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(passada_response.status_code, status.HTTP_409_CONFLICT)

    def test_sincronizacao_de_aulas_ignora_datas_passadas_e_recusa_periodo_encerrado(self):
        hoje = timezone.localdate()
        periodo = PeriodoLetivo.objects.create(
            nome="Periodo atual",
            data_inicio=hoje - timedelta(days=14),
            data_fim=hoje + timedelta(days=14),
            ativo=True,
        )
        turma = self.criar_turma("SYNC", periodo, self.disciplina, self.professor)
        horario = HorarioPadraoUFMA.objects.create(
            codigo=f"{hoje.weekday() + 2}N12",
            dia_semana=hoje.weekday() + 2,
            horario_inicio=time(18, 0),
            horario_fim=time(20, 0),
        )

        sincronizar_aulas_da_turma(turma, [{"sala": self.sala, "horario_padrao": horario}])

        self.assertTrue(Aula.objects.filter(turma=turma).exists())
        self.assertTrue(all(aula.data >= hoje for aula in Aula.objects.filter(turma=turma)))

        periodo_encerrado = PeriodoLetivo.objects.create(
            nome="Periodo encerrado",
            data_inicio=hoje - timedelta(days=30),
            data_fim=hoje - timedelta(days=1),
            ativo=True,
        )
        turma_encerrada = self.criar_turma("OLD", periodo_encerrado, self.disciplina, self.professor)
        with self.assertRaises(DomainValidationError):
            sincronizar_aulas_da_turma(turma_encerrada, [{"sala": self.sala, "horario_padrao": horario}])

    def test_edge_node_aceita_presenca_no_horario_sem_gravar_status(self):
        aula = self.criar_aula(self.turma, timezone.localdate(), Aula.STATUS_ABERTA)
        no = NoBorda.objects.create(codigo="NO-EDGE", nome="No Edge")
        _, token = TokenNoBorda.emitir_token(no, nome="teste")
        dispositivo = DispositivoEsp32.objects.create(no=no, sala=self.sala, codigo="ESP-EDGE", nome="ESP Edge")
        reconhecido_em = aula.inicio + timedelta(minutes=10)

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
                        "reconhecido_em": reconhecido_em.isoformat(),
                        "score": 0.95,
                    }
                ],
            },
            format="json",
            HTTP_X_NODE_TOKEN=token,
        )

        aula.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(status_aula(aula), Aula.STATUS_ABERTA)
        self.assertTrue(RegistroPresenca.objects.filter(aula=aula, aluno=self.aluno).exists())

    @override_settings(FACE_EMBEDDING_ENCRYPTION_KEY=FERNET_TEST_KEY)
    def test_edge_pull_envia_embedding_criptografado_sem_vetor_claro(self):
        from api.services.sincronizacao_borda import montar_payload_pull

        no = NoBorda.objects.create(codigo="NO-EDGE-PULL", nome="No Edge Pull")
        DispositivoEsp32.objects.create(no=no, sala=self.sala, codigo="ESP-PULL", nome="ESP Pull")
        self.criar_aula(self.turma, timezone.localdate(), Aula.STATUS_ABERTA)
        embedding = EmbeddingFacial.objects.create(
            aluno=self.aluno,
            versao_modelo="sface",
            vetor=criptografar_vetor([0.1, 0.2]),
            status=EmbeddingFacial.STATUS_ATIVO,
            ativo=True,
        )

        payload = montar_payload_pull(no, {})
        embedding_payload = payload["cache_redis"]["embeddings_faciais"][str(embedding.id)]

        self.assertIn("embedding_encrypted", embedding_payload)
        self.assertNotIn("embedding", embedding_payload)
        self.assertIsInstance(embedding_payload["embedding_encrypted"], str)
        self.assertNotIn("data", embedding_payload["embedding_encrypted"])

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
        token_antigo.refresh_from_db()
        self.assertFalse(token_antigo.ativo)
        self.assertTrue(TokenNoBorda.objects.filter(id=token_integracao.id).exists())
        self.assertEqual(TokenNoBorda.objects.filter(no=no, nome="visualizacao-unica", ativo=True).count(), 1)
        self.assertEqual(TokenNoBorda.objects.get(no=no, nome="visualizacao-unica", ativo=True).prefixo_token, response.data["prefixo_token"])

    def test_delete_academico_desativa_sem_apagar_historico(self):
        aula = self.criar_aula(self.turma, timezone.localdate() + timedelta(days=1), Aula.STATUS_PLANEJADA)
        matricula = MatriculaTurma.objects.get(turma=self.turma, aluno=self.aluno)

        self.autenticar(self.admin)
        turma_response = self.client.delete(f"/api/turmas/{self.turma.id}/")
        matricula_response = self.client.delete(f"/api/matriculas-turma/{matricula.id}/")
        usuario_response = self.client.delete(f"/api/usuarios/{self.outro_aluno.id}/")

        self.assertEqual(turma_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(matricula_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(usuario_response.status_code, status.HTTP_204_NO_CONTENT)
        self.turma.refresh_from_db()
        matricula.refresh_from_db()
        self.outro_aluno.refresh_from_db()
        aula.refresh_from_db()
        self.assertFalse(self.turma.ativo)
        self.assertFalse(matricula.ativo)
        self.assertFalse(self.outro_aluno.is_active)
        self.assertEqual(status_aula(aula), Aula.STATUS_CANCELADA)
        self.assertIsNotNone(aula.cancelada_em)

    def test_biometria_lista_e_revoga_sem_consentimento_explicito(self):
        embedding = EmbeddingFacial.objects.create(
            aluno=self.aluno,
            versao_modelo="sface",
            vetor=[0.1, 0.2],
            status=EmbeddingFacial.STATUS_ATIVO,
            ativo=True,
        )

        self.autenticar(self.aluno)
        list_response = self.client.get("/api/me/biometrias/")
        delete_response = self.client.delete(f"/api/me/biometrias/{embedding.id}/")
        after_response = self.client.get("/api/me/biometrias/")

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertTrue(list_response.data["biometrias"][0]["possui_vetor"])
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        embedding.refresh_from_db()
        self.assertFalse(embedding.ativo)
        self.assertEqual(embedding.status, EmbeddingFacial.STATUS_REVOGADO)
        self.assertEqual(embedding.vetor, [])
        self.assertFalse(after_response.data["biometrias"][0]["possui_vetor"])
