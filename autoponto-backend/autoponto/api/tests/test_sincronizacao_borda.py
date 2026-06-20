from datetime import date, datetime, time
from unittest.mock import patch

import msgpack
from django.test import TestCase
from django.utils import timezone

from api.models import (
    Aula,
    Campus,
    Curso,
    Disciplina,
    DispositivoEsp32,
    HorarioPadraoUFMA,
    MatriculaTurma,
    NoBorda,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    Sala,
    Turma,
    Usuario,
)
from api.serializers.edge import EdgeAulaSerializer
from api.services.sincronizacao_borda import montar_payload_pull


class SincronizacaoBordaContratoTests(TestCase):
    def setUp(self):
        self.data_aula = date(2026, 6, 20)
        campus = Campus.objects.create(nome="Campus Sao Luis")
        predio = Predio.objects.create(campus=campus, nome="CCET")
        self.sala = Sala.objects.create(predio=predio, nome="Laboratorio 1", codigo="LAB1")
        curso = Curso.objects.create(campus=campus, nome="Engenharia da Computacao")
        disciplina = Disciplina.objects.create(
            curso=curso,
            codigo="CP001",
            nome="Sistemas Embarcados",
        )
        periodo = PeriodoLetivo.objects.create(
            nome="2026.1",
            data_inicio=date(2026, 6, 1),
            data_fim=date(2026, 6, 30),
            ativo=True,
        )
        self.turma = Turma.objects.create(
            periodo_letivo=periodo,
            disciplina=disciplina,
            codigo="01",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno",
            password="senha",
            papel=PapelUsuario.ALUNO,
            matricula="20260001",
            nome_completo="Aluno Teste",
        )
        self.matricula = MatriculaTurma.objects.create(turma=self.turma, aluno=self.aluno)
        self.no = NoBorda.objects.create(codigo="NO-CCET-01", nome="No CCET")
        self.dispositivo = DispositivoEsp32.objects.create(
            no=self.no,
            sala=self.sala,
            codigo="ESP32-LAB1",
            nome="ESP32 Lab 1",
            interscity_uuid="uuid-interscity",
        )
        horario = HorarioPadraoUFMA.objects.create(
            codigo="7M12",
            dia_semana=HorarioPadraoUFMA.DiaSemana.SABADO,
            horario_inicio=time(8, 0),
            horario_fim=time(9, 40),
        )
        self.aula = Aula.objects.create(
            turma=self.turma,
            sala=self.sala,
            horario_padrao=horario,
            data=self.data_aula,
            inicio=timezone.make_aware(datetime(2026, 6, 20, 8, 0)),
            fim=timezone.make_aware(datetime(2026, 6, 20, 9, 40)),
        )

    def _pull(self, params):
        with patch(
            "api.services.sincronizacao_borda.timezone.localdate",
            return_value=self.data_aula,
        ):
            return montar_payload_pull(self.no, params)

    def test_pull_completo_usa_matriculas_turma_e_aula_aponta_para_turma(self):
        resposta = self._pull({"node_id": self.no.codigo, "full": "true"})

        self.assertIn("matriculas_turma", resposta["data"])
        self.assertNotIn("matriculas_aula", resposta["data"])
        self.assertNotIn("matriculas_aula", resposta["deleted"])
        self.assertEqual(set(resposta), {"data", "deleted", "cursors"})
        self.assertNotIn("cursor", resposta)
        self.assertEqual(set(resposta["cursors"]), set(resposta["data"]))

        aula = resposta["data"]["aulas"][0]
        matricula = resposta["data"]["matriculas_turma"][0]

        self.assertEqual(aula["id"], str(self.aula.id))
        self.assertEqual(aula["turma_id"], str(self.turma.id))
        self.assertEqual(matricula["id"], str(self.matricula.id))
        self.assertEqual(matricula["turma_id"], str(self.turma.id))
        self.assertEqual(matricula["aluno_id"], str(self.aluno.id))

    def test_serializer_edge_de_aula_expõe_apenas_campos_do_contrato(self):
        self.assertEqual(
            set(EdgeAulaSerializer(self.aula).data),
            {"id", "nome", "turma_id", "sala_id", "inicio", "fim", "status"},
        )

    def test_incremental_de_matricula_turma_retorna_uuid_real_da_matricula(self):
        cursors = self._pull({"node_id": self.no.codigo, "full": "true"})["cursors"]
        outro_aluno = Usuario.objects.create_user(
            username="outro-aluno",
            password="senha",
            papel=PapelUsuario.ALUNO,
            matricula="20260002",
            nome_completo="Outro Aluno",
        )
        nova_matricula = MatriculaTurma.objects.create(
            turma=self.turma,
            aluno=outro_aluno,
        )

        resposta = self._pull(
            {"node_id": self.no.codigo, "cursors": msgpack.packb(cursors).hex()}
        )

        self.assertIn("matriculas_turma", resposta["data"])
        self.assertEqual(
            [item["id"] for item in resposta["data"]["matriculas_turma"]],
            [str(nova_matricula.id)],
        )
        self.assertEqual(resposta["deleted"]["matriculas_turma"], [])

    def test_incremental_de_matricula_nao_reenvia_contexto_relacionado(self):
        cursors = self._pull({"node_id": self.no.codigo, "full": "true"})["cursors"]

        self.matricula.save()

        resposta = self._pull(
            {"node_id": self.no.codigo, "cursors": msgpack.packb(cursors).hex()}
        )

        self.assertEqual(resposta["data"]["aulas"], [])
        self.assertEqual(resposta["data"]["alunos"], [])
        self.assertEqual(resposta["data"]["embeddings_faciais"], [])
        self.assertEqual(
            [item["id"] for item in resposta["data"]["matriculas_turma"]],
            [str(self.matricula.id)],
        )

    def test_delete_de_matricula_turma_remove_uuid_real_da_matricula(self):
        cursors = self._pull({"node_id": self.no.codigo, "full": "true"})["cursors"]
        matricula_id = str(self.matricula.id)

        self.matricula.delete()

        resposta = self._pull(
            {"node_id": self.no.codigo, "cursors": msgpack.packb(cursors).hex()}
        )

        self.assertEqual(resposta["data"]["matriculas_turma"], [])
        self.assertEqual(resposta["deleted"]["matriculas_turma"], [matricula_id])

    def test_full_sync_aceita_somente_true_explicito(self):
        with self.assertRaisesMessage(Exception, "Use full=true"):
            self._pull({"node_id": self.no.codigo, "full": "1"})
