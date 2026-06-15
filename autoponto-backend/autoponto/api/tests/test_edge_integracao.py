from datetime import datetime, timezone
from unittest.mock import patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import (
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
        self.assertEqual(set(aula.keys()), {"id", "name", "locale_id", "starts_at", "ends_at", "status"})
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

    def test_envio_de_presenca_fora_da_duracao_da_aula_e_rejeitado(self):
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
                        "recognized_at": "2026-04-20T10:00:00-03:00",
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
                        "recognized_at": "2026-04-20T08:05:00-03:00",
                        "score": 0.91,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(RegistroPresenca.objects.count(), 0)

    @override_settings(INTERSCITY_ENABLED=True)
    @patch("api.services.interscity.urlopen")
    def test_status_dispositivo_atualiza_snapshot_local_e_publica_no_interscity(self, urlopen):
        self.contexto["dispositivo"].interscity_uuid = "0dbdae10-4156-4433-9291-5d261eb0d8eb"
        self.contexto["dispositivo"].save(update_fields=["interscity_uuid", "atualizado_em"])

        resposta = self.client.post(
            "/api/edge/devices/status/",
            {
                "node_id": self.no.codigo,
                "devices": [
                    {
                        "device_id": str(self.contexto["dispositivo"].id),
                        "status": "working",
                        "reported_at": "2026-04-20T10:00:00Z",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["updated_ids"], [str(self.contexto["dispositivo"].id)])
        self.contexto["dispositivo"].refresh_from_db()
        self.assertEqual(self.contexto["dispositivo"].status, "working")
        self.assertIsNotNone(self.contexto["dispositivo"].status_atualizado_em)
        requisicao = urlopen.call_args.args[0]
        self.assertIn("/adaptor/resources/0dbdae10-4156-4433-9291-5d261eb0d8eb/data", requisicao.full_url)
        self.assertIn(b"autoponto_device_status", requisicao.data)

    def test_status_dispositivo_rejeita_dispositivo_de_outro_no(self):
        outro_no = NoBorda.objects.create(codigo="NO-CCET-02", nome="Raspberry CCET 02")
        self.contexto["dispositivo"].no = outro_no
        self.contexto["dispositivo"].save(update_fields=["no", "atualizado_em"])

        resposta = self.client.post(
            "/api/edge/devices/status/",
            {
                "node_id": self.no.codigo,
                "devices": [
                    {
                        "device_id": str(self.contexto["dispositivo"].id),
                        "status": "idle",
                        "reported_at": "2026-04-20T10:00:00Z",
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
