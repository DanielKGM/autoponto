import json
from unittest.mock import patch

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .helpers import criar_contexto_academico


class RespostaHTTPFake:
    status = 200

    def __init__(self, corpo: dict):
        self.corpo = json.dumps(corpo).encode("utf-8")

    def read(self):
        return self.corpo

    def close(self):
        pass


class MapaPublicoTests(APITestCase):
    def setUp(self):
        self.contexto = criar_contexto_academico()
        self.dispositivo = self.contexto["dispositivo"]
        self.dispositivo.interscity_uuid = "f3e29da0-e958-4f6a-90eb-cef7804cd28c"
        self.dispositivo.latitude = "-2.558300"
        self.dispositivo.longitude = "-44.307700"
        self.dispositivo.save(update_fields=["interscity_uuid", "latitude", "longitude", "atualizado_em"])

    def test_mapa_publico_lista_apenas_esps_ativas_com_recurso_e_localizacao(self):
        resposta = self.client.get("/api/public/mapa/dispositivos/")

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resposta.data), 1)
        self.assertEqual(resposta.data[0]["id"], str(self.dispositivo.id))
        self.assertEqual(resposta.data[0]["codigo"], self.dispositivo.codigo)
        self.assertEqual(resposta.data[0]["sala"], self.contexto["sala"].nome)
        self.assertEqual(resposta.data[0]["predio"], self.contexto["predio"].nome)
        self.assertEqual(resposta.data[0]["latitude"], "-2.558300")
        self.assertEqual(resposta.data[0]["longitude"], "-44.307700")
        self.assertEqual(resposta.data[0]["interscity_uuid"], self.dispositivo.interscity_uuid)

    @override_settings(
        INTERSCITY_ENABLED=True,
        INTERSCITY_BASE_URL="http://interscity.example",
        INTERSCITY_COLLECTOR_PATH="/collector",
        INTERSCITY_TIMEOUT_SECONDS=5,
    )
    @patch("api.services.interscity.urlopen")
    def test_historico_publico_consulta_collector_com_capacidades_permitidas(self, urlopen):
        urlopen.return_value = RespostaHTTPFake(
            {
                "resources": [
                    {
                        "uuid": self.dispositivo.interscity_uuid,
                        "capabilities": {
                            "status": [
                                {"value": "idle", "date": "2026-06-18T10:00:00.000Z"},
                                {"value": "working", "date": "2026-06-19T10:00:00.000Z"},
                            ],
                            "rssi": [{"value": -61, "date": "2026-06-19T10:00:00.000Z"}],
                            "air_quality_index": [{"value": 12, "date": "2026-06-19T10:00:00.000Z"}],
                        },
                    }
                ]
            }
        )

        resposta = self.client.get(f"/api/public/mapa/dispositivos/{self.dispositivo.id}/historico/", {"dias": "7"})

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["collector_status"], "ok")
        self.assertEqual(resposta.data["dispositivo"]["id"], str(self.dispositivo.id))
        self.assertEqual(resposta.data["historico"]["status"][0]["value"], "idle")
        self.assertEqual(resposta.data["ultimo"]["status"]["value"], "working")
        self.assertEqual(resposta.data["ultimo"]["rssi"]["value"], -61)
        self.assertNotIn("air_quality_index", resposta.data["historico"])

        requisicao = urlopen.call_args.args[0]
        self.assertEqual(requisicao.full_url, "http://interscity.example/collector/resources/data")
        corpo = json.loads(requisicao.data.decode("utf-8"))
        self.assertEqual(corpo["uuids"], [self.dispositivo.interscity_uuid])
        self.assertIn("status", corpo["capabilities"])
        self.assertIn("rssi", corpo["capabilities"])
        self.assertIn("start_date", corpo)
        self.assertIn("end_date", corpo)

    @override_settings(INTERSCITY_ENABLED=False)
    @patch("api.services.interscity.urlopen")
    def test_historico_publico_nao_quebra_quando_collector_desabilitado(self, urlopen):
        resposta = self.client.get(f"/api/public/mapa/dispositivos/{self.dispositivo.id}/historico/")

        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["collector_status"], "nao_configurado")
        self.assertEqual(resposta.data["historico"], {})
        self.assertEqual(resposta.data["ultimo"], {})
        urlopen.assert_not_called()
