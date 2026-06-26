from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.test import APITestCase

from api.models import (
    Aula,
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    HorarioPadraoUFMA,
    NoBorda,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    Sala,
    Turma,
    Usuario,
)
from api.selectors.aulas import com_status_aula, status_aula


class StatusAulasDerivadoTests(APITestCase):
    def setUp(self):
        self.professor = Usuario.objects.create_user(
            username="prof-status",
            password="senha",
            papel=PapelUsuario.PROFESSOR,
            matricula="",
        )
        self.campus = Campus.objects.create(nome="Campus")
        predio = Predio.objects.create(campus=self.campus, nome="Predio")
        self.curso = Curso.objects.create(nome="Curso", campus=self.campus)
        self.disciplina = Disciplina.objects.create(
            nome="Disciplina",
            codigo="DISC",
            curso=self.curso,
        )
        self.periodo = PeriodoLetivo.objects.create(
            nome="Periodo status",
            data_inicio=timezone.localdate() - timedelta(days=30),
            data_fim=timezone.localdate() + timedelta(days=30),
            ativo=True,
        )
        self.turma = Turma.objects.create(
            disciplina=self.disciplina,
            periodo_letivo=self.periodo,
            codigo="T1",
        )
        self.turma.professores.add(self.professor)
        self.sala = Sala.objects.create(nome="Sala 1", codigo="101", predio=predio)

    def _horario(self, inicio, fim):
        dia_semana = inicio.weekday() + 2
        indice = HorarioPadraoUFMA.objects.count() + 1
        return HorarioPadraoUFMA.objects.create(
            codigo=f"{dia_semana}M{(indice % 6) + 1}{((indice + 1) % 6) + 1}",
            dia_semana=dia_semana,
            horario_inicio=inicio.time().replace(second=0, microsecond=0),
            horario_fim=fim.time().replace(second=0, microsecond=0),
        )

    def _aula(self, inicio, fim, **kwargs):
        return Aula.objects.create(
            turma=self.turma,
            sala=self.sala,
            horario_padrao=self._horario(inicio, fim),
            data=inicio.date(),
            inicio=inicio,
            fim=fim,
            **kwargs,
        )

    def test_selector_deriva_status_sem_cron(self):
        agora = timezone.now()
        futura = self._aula(agora + timedelta(hours=2), agora + timedelta(hours=3))
        atual = self._aula(agora - timedelta(minutes=15), agora + timedelta(minutes=45))
        passada = self._aula(agora - timedelta(hours=3), agora - timedelta(hours=2))
        cancelada = self._aula(
            agora - timedelta(hours=5),
            agora - timedelta(hours=4),
            cancelada_em=agora - timedelta(hours=4, minutes=30),
            cancelada_por=self.professor,
        )
        fechada_manual = self._aula(
            agora + timedelta(hours=5),
            agora + timedelta(hours=6),
            fechada_em=agora,
            fechada_por=self.professor,
        )

        self.assertEqual(status_aula(futura, agora), Aula.STATUS_PLANEJADA)
        self.assertEqual(status_aula(atual, agora), Aula.STATUS_ABERTA)
        self.assertEqual(status_aula(passada, agora), Aula.STATUS_FECHADA)
        self.assertEqual(status_aula(cancelada, agora), Aula.STATUS_CANCELADA)
        self.assertEqual(status_aula(fechada_manual, agora), Aula.STATUS_FECHADA)

        anotadas = {
            aula.id: aula.status
            for aula in com_status_aula(
                Aula.objects.filter(
                    id__in=[futura.id, atual.id, passada.id, cancelada.id, fechada_manual.id]
                ),
                agora=agora,
            )
        }

        self.assertEqual(anotadas[futura.id], Aula.STATUS_PLANEJADA)
        self.assertEqual(anotadas[atual.id], Aula.STATUS_ABERTA)
        self.assertEqual(anotadas[passada.id], Aula.STATUS_FECHADA)
        self.assertEqual(anotadas[cancelada.id], Aula.STATUS_CANCELADA)
        self.assertEqual(anotadas[fechada_manual.id], Aula.STATUS_FECHADA)

    def test_cancelada_e_fechada_sao_mutuamente_exclusivas(self):
        agora = timezone.now()
        inicio = agora + timedelta(hours=1)
        fim = agora + timedelta(hours=2)
        aula = Aula(
            turma=self.turma,
            sala=self.sala,
            horario_padrao=self._horario(inicio, fim),
            data=inicio.date(),
            inicio=inicio,
            fim=fim,
            cancelada_em=agora,
            cancelada_por=self.professor,
            fechada_em=agora,
            fechada_por=self.professor,
        )

        with self.assertRaises(ValidationError):
            aula.full_clean()

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._aula(
                    agora + timedelta(hours=3),
                    agora + timedelta(hours=4),
                    cancelada_em=agora,
                    cancelada_por=self.professor,
                    fechada_em=agora,
                    fechada_por=self.professor,
                )

    def test_api_filtra_por_status_derivado(self):
        agora = timezone.now()
        atual = self._aula(agora - timedelta(minutes=10), agora + timedelta(minutes=50))
        passada = self._aula(agora - timedelta(hours=4), agora - timedelta(hours=3))
        cancelada = self._aula(
            agora - timedelta(hours=6),
            agora - timedelta(hours=5),
            cancelada_em=agora - timedelta(hours=5, minutes=30),
            cancelada_por=self.professor,
        )

        self.client.force_authenticate(self.professor)

        abertas = self.client.get("/api/aulas/", {"status": Aula.STATUS_ABERTA})
        self.assertEqual(abertas.status_code, http_status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in abertas.data["results"]], [atual.id])
        self.assertEqual(abertas.data["results"][0]["status"], Aula.STATUS_ABERTA)

        fechadas = self.client.get("/api/aulas/", {"status": Aula.STATUS_FECHADA})
        self.assertEqual(fechadas.status_code, http_status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in fechadas.data["results"]], [passada.id])
        self.assertEqual(fechadas.data["results"][0]["status"], Aula.STATUS_FECHADA)

        canceladas = self.client.get("/api/aulas/", {"status": Aula.STATUS_CANCELADA})
        self.assertEqual(canceladas.status_code, http_status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in canceladas.data["results"]], [cancelada.id])
        self.assertEqual(canceladas.data["results"][0]["status"], Aula.STATUS_CANCELADA)

    def test_sync_nao_envia_vencida_cancelada_e_aceita_presenca_no_horario(self):
        from api.services.sincronizacao_borda import montar_payload_pull

        agora = timezone.now()
        no = NoBorda.objects.create(
            codigo="edge-status",
            nome="Edge Status",
        )
        DispositivoEsp32.objects.create(
            no=no,
            sala=self.sala,
            codigo="esp-status",
            nome="ESP Status",
        )

        atual = self._aula(agora - timedelta(minutes=10), agora + timedelta(minutes=50))
        self._aula(agora - timedelta(hours=4), agora - timedelta(hours=3))
        self._aula(
            agora + timedelta(hours=1),
            agora + timedelta(hours=2),
            cancelada_em=agora,
            cancelada_por=self.professor,
        )

        payload = montar_payload_pull(no, {})
        aulas_payload = payload["cache_redis"]["aulas_por_sala"].get(str(self.sala.id), [])

        self.assertEqual([item["id"] for item in aulas_payload], [str(atual.id)])
        self.assertEqual(aulas_payload[0]["status"], Aula.STATUS_ABERTA)
