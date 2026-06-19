from datetime import datetime, timezone
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
        self.contexto["dispositivo"].interscity_uuid = "f3e29da0-e958-4f6a-90eb-cef7804cd28c"
        self.contexto["dispositivo"].save(update_fields=["no", "interscity_uuid", "atualizado_em"])
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
                "cursors": "80",
                "from_date": "2026-04-20",
                "to_date": "2026-04-20",
            },
        )

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        payload = resposta.data
        self.assertEqual(set(payload.keys()), {"data", "deleted", "cursors"})
        self.assertEqual(
            set(payload["data"].keys()),
            {"salas", "dispositivos", "aulas", "alunos", "matriculas_aula", "embeddings_faciais"},
        )
        self.assertEqual(set(payload["deleted"].keys()), set(payload["data"].keys()))
        self.assertEqual(set(payload["cursors"].keys()), set(payload["data"].keys()))
        self.assertEqual(payload["data"]["salas"][0], {"id": str(self.contexto["sala"].id), "nome": self.contexto["sala"].nome})
        self.assertEqual(payload["data"]["dispositivos"][0]["id"], self.contexto["dispositivo"].codigo)
        self.assertEqual(payload["data"]["dispositivos"][0]["sala_id"], str(self.contexto["sala"].id))
        self.assertEqual(payload["data"]["dispositivos"][0]["ativo"], True)
        self.assertEqual(payload["data"]["dispositivos"][0]["interscity_uuid"], self.contexto["dispositivo"].interscity_uuid)
        self.assertNotIn("status", payload["data"]["dispositivos"][0])
        self.assertEqual(payload["data"]["alunos"][0]["matricula"], self.contexto["aluno"].matricula)
        self.assertNotIn("ativo", payload["data"]["alunos"][0])
        self.assertEqual(payload["data"]["embeddings_faciais"][0]["vetor"], self.embedding.vetor)

        aula = payload["data"]["aulas"][0]
        self.assertEqual(aula["sala_id"], str(self.contexto["sala"].id))
        self.assertIn("Desenvolvimento de Sistemas Web", aula["nome"])
        self.assertEqual(
            payload["data"]["matriculas_aula"][0],
            {"aula_id": aula["id"], "aluno_id": str(self.contexto["aluno"].id)},
        )
        self.assertEqual(set(aula.keys()), {"id", "nome", "sala_id", "inicio", "fim", "status"})
        self.assertEqual(aula["status"], "PLANEJADA")
        self.assertIn("aulas", payload["cursors"])

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
        self.assertEqual(resposta.data["data"]["dispositivos"], [])
        self.assertIn(self.contexto["dispositivo"].codigo, resposta.data["deleted"]["dispositivos"])

    def test_envio_de_presenca_e_idempotente_e_confirma_synced_ids(self):
        aula_id = self.client.get(
            "/api/edge/pull",
            {
                "node_id": self.no.codigo,
                "from_date": "2026-04-20",
                "to_date": "2026-04-20",
            },
        ).data["data"]["aulas"][0]["id"]
        evento = {
            "id": "edge-event-1",
            "aluno_id": str(self.contexto["aluno"].id),
            "aula_id": aula_id,
            "dispositivo_id": self.contexto["dispositivo"].codigo,
            "reconhecido_em": datetime(2026, 4, 20, 11, 5, tzinfo=timezone.utc).isoformat(),
            "score": 0.91,
        }

        primeira = self.client.post("/api/edge/attendance", {"node_id": self.no.codigo, "eventos": [evento]}, format="json")
        segunda = self.client.post("/api/edge/attendance", {"node_id": self.no.codigo, "eventos": [evento]}, format="json")

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
        ).data["data"]["aulas"][0]["id"]

        resposta = self.client.post(
            "/api/edge/attendance",
            {
                "node_id": self.no.codigo,
                "eventos": [
                    {
                        "id": "edge-event-fora",
                        "aluno_id": str(self.contexto["aluno"].id),
                        "aula_id": aula_id,
                        "dispositivo_id": self.contexto["dispositivo"].codigo,
                        "reconhecido_em": "2026-04-20T10:00:00-03:00",
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
        ).data["data"]["aulas"][0]["id"]
        outro_no = NoBorda.objects.create(codigo="NO-CCET-02", nome="Raspberry CCET 02")
        dispositivo = self.contexto["dispositivo"]
        dispositivo.no = outro_no
        dispositivo.save(update_fields=["no", "atualizado_em"])
        resposta = self.client.post(
            "/api/edge/attendance",
            {
                "node_id": self.no.codigo,
                "eventos": [
                    {
                        "id": "edge-event-2",
                        "aluno_id": str(self.contexto["aluno"].id),
                        "aula_id": aula_id,
                        "dispositivo_id": dispositivo.codigo,
                        "reconhecido_em": "2026-04-20T08:05:00-03:00",
                        "score": 0.91,
                    }
                ],
            },
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(RegistroPresenca.objects.count(), 0)

    def test_status_dispositivo_nao_faz_parte_do_contrato_ativo(self):
        resposta = self.client.post(
            "/api/edge/devices/status/",
            {"node_id": self.no.codigo, "devices": []},
            format="json",
        )

        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
