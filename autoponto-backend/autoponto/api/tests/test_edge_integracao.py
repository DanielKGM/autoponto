from datetime import datetime, timezone

from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
    ComandoBorda,
    EmbeddingFacial,
    EventoReconhecimento,
    NoBorda,
    PerfilBiometrico,
    RegistroPresenca,
    TokenNoBorda,
)
from .helpers import criar_contexto_academico


class IntegracaoEdgeTests(APITestCase):
    def setUp(self):
        self.contexto = criar_contexto_academico()
        self.no = NoBorda.objects.create(codigo="NO-CCET-01", nome="Raspberry CCET 01")
        self.contexto["dispositivo"].no = self.no
        self.contexto["dispositivo"].save(update_fields=["no", "atualizado_em"])
        _, self.token_bruto = TokenNoBorda.emitir_token(self.no, nome="teste-no")
        self.client.credentials(HTTP_AUTHORIZATION=f"NodeToken {self.token_bruto}")

        perfil = PerfilBiometrico.objects.create(aluno=self.contexto["aluno"], status="ATIVO")
        self.embedding = EmbeddingFacial.objects.create(
            perfil=perfil,
            versao_modelo="sface-v1",
            vetor=[0.01, 0.02, 0.03, 0.04],
            status="ATIVO",
            ativo=True,
        )

    def test_pull_do_no_retorna_payload_compativel_com_edge(self):
        resposta = self.client.get(
            "/api/edge/pull",
            {
                "node_id": self.no.codigo,
                "from_date": "2026-04-20",
                "to_date": "2026-04-20",
            },
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        payload = resposta.data
        self.assertEqual(set(payload.keys()), {"data", "deleted", "cursors"})
        self.assertEqual(payload["data"]["locales"][0]["id"], str(self.contexto["sala"].id))
        self.assertEqual(payload["data"]["devices"][0]["id"], str(self.contexto["dispositivo"].id))
        self.assertEqual(payload["data"]["devices"][0]["locale_id"], str(self.contexto["sala"].id))
        self.assertEqual(payload["data"]["students"][0]["registration"], self.contexto["aluno"].matricula)
        self.assertEqual(payload["data"]["face_embeddings"][0]["embedding"], self.embedding.vetor)

        aula = payload["data"]["lessons"][0]
        self.assertEqual(aula["locale_id"], str(self.contexto["sala"].id))
        self.assertIn("Desenvolvimento de Sistemas Web", aula["name"])
        self.assertEqual(
            payload["data"]["enrollments"][0],
            {"lesson_id": aula["id"], "student_id": str(self.contexto["aluno"].id)},
        )
        self.assertIn("attendance_starts_at", aula)
        self.assertIn("attendance_ends_at", aula)
        self.assertEqual(aula["status"], "PLANEJADA")
        self.assertIn("lessons", payload["cursors"])

    def test_pull_incremental_informa_dispositivo_inativo_como_deleted(self):
        self.contexto["dispositivo"].ativo = False
        self.contexto["dispositivo"].save(update_fields=["ativo", "atualizado_em"])

        resposta = self.client.get(
            "/api/edge/pull",
            {
                "node_id": self.no.codigo,
                "from_date": "2026-04-20",
                "to_date": "2026-04-20",
            },
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["data"]["devices"], [])
        self.assertIn(str(self.contexto["dispositivo"].id), resposta.data["deleted"]["devices"])

    def test_envio_de_presenca_e_idempotente_e_confirma_synced_ids(self):
        aula_id = self.client.get(
            "/api/edge/pull",
            {
                "node_id": self.no.codigo,
                "from_date": "2026-04-20",
                "to_date": "2026-04-20",
            },
        ).data["data"]["lessons"][0]["id"]
        evento = {
            "id": "edge-event-1",
            "student_id": str(self.contexto["aluno"].id),
            "lesson_id": aula_id,
            "device_id": str(self.contexto["dispositivo"].id),
            "recognized_at": datetime(2026, 4, 20, 11, 5, tzinfo=timezone.utc).isoformat(),
            "score": 0.91,
        }

        primeira = self.client.post("/api/edge/attendance", {"node_id": self.no.codigo, "events": [evento]}, format="json")
        segunda = self.client.post("/api/edge/attendance", {"node_id": self.no.codigo, "events": [evento]}, format="json")

        self.assertEqual(primeira.status_code, status.HTTP_200_OK)
        self.assertEqual(segunda.status_code, status.HTTP_200_OK)
        self.assertEqual(primeira.data["synced_ids"], ["edge-event-1"])
        self.assertEqual(segunda.data["synced_ids"], ["edge-event-1"])
        self.assertEqual(RegistroPresenca.objects.count(), 1)
        self.assertEqual(EventoReconhecimento.objects.count(), 1)
        self.assertEqual(EventoReconhecimento.objects.get().id_evento_origem, "edge-event-1")

    def test_envio_de_presenca_fora_da_janela_e_rejeitado(self):
        horario = self.contexto["horario"]
        horario.fecha_chamada_minutos = 30
        horario.save(update_fields=["fecha_chamada_minutos", "atualizado_em"])
        aula_id = self.client.get(
            "/api/edge/pull",
            {"node_id": self.no.codigo, "from_date": "2026-04-20", "to_date": "2026-04-20"},
        ).data["data"]["lessons"][0]["id"]

        resposta = self.client.post(
            "/api/edge/attendance",
            {
                "node_id": self.no.codigo,
                "events": [
                    {
                        "id": "edge-event-fora",
                        "student_id": str(self.contexto["aluno"].id),
                        "lesson_id": aula_id,
                        "device_id": str(self.contexto["dispositivo"].id),
                        "recognized_at": "2026-04-20T12:00:00+00:00",
                        "score": 0.91,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(RegistroPresenca.objects.count(), 0)

    def test_envio_de_presenca_rejeita_dispositivo_de_outro_no(self):
        aula_id = self.client.get(
            "/api/edge/pull",
            {"node_id": self.no.codigo, "from_date": "2026-04-20", "to_date": "2026-04-20"},
        ).data["data"]["lessons"][0]["id"]
        outro_no = NoBorda.objects.create(codigo="NO-CCET-02", nome="Raspberry CCET 02")
        dispositivo = self.contexto["dispositivo"]
        dispositivo.no = outro_no
        dispositivo.save(update_fields=["no", "atualizado_em"])
        resposta = self.client.post(
            "/api/edge/attendance",
            {
                "node_id": self.no.codigo,
                "events": [
                    {
                        "id": "edge-event-2",
                        "student_id": str(self.contexto["aluno"].id),
                        "lesson_id": aula_id,
                        "device_id": str(dispositivo.id),
                        "recognized_at": "2026-04-20T11:05:00+00:00",
                        "score": 0.91,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(RegistroPresenca.objects.count(), 0)

    def test_webhook_interscity_cria_comando_e_ack_do_no_marca_entregue(self):
        self.contexto["dispositivo"].interscity_uuid = "0dbdae10-4156-4433-9291-5d261eb0d8eb"
        self.contexto["dispositivo"].save(update_fields=["interscity_uuid", "atualizado_em"])
        self.client.credentials()

        webhook = self.client.post(
            "/api/interscity/webhooks/actuator/",
            {
                "action": "actuator_command",
                "command": {
                    "_id": {"$oid": "59395c1329d4b10379bed679"},
                    "uuid": "0dbdae10-4156-4433-9291-5d261eb0d8eb",
                    "capability": "autoponto_edge_command",
                    "value": {"type": "display_message", "payload": {"message": "Chamada aberta"}},
                    "created_at": "2026-04-20T10:00:00Z",
                },
            },
            format="json",
        )

        self.assertEqual(webhook.status_code, status.HTTP_202_ACCEPTED)
        comando = ComandoBorda.objects.get()
        self.assertEqual(comando.no, self.no)
        self.assertEqual(comando.dispositivo, self.contexto["dispositivo"])
        self.assertEqual(comando.status, "PENDENTE")
        self.assertIsNone(comando.criado_por)

        self.client.credentials(HTTP_AUTHORIZATION=f"NodeToken {self.token_bruto}")
        comandos = self.client.get("/api/edge/commands", {"node_id": self.no.codigo})
        self.assertEqual(comandos.status_code, status.HTTP_200_OK)
        self.assertEqual(comandos.data["commands"][0]["id"], str(comando.id))

        ack = self.client.post(
            "/api/edge/commands/ack",
            {
                "node_id": self.no.codigo,
                "commands": [{"id": str(comando.id), "status": "DELIVERED"}],
            },
            format="json",
        )
        self.assertEqual(ack.status_code, status.HTTP_200_OK)
        comando.refresh_from_db()
        self.assertEqual(comando.status, "ENTREGUE")
