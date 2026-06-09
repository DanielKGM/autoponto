from unittest.mock import patch
from socket import timeout
from urllib.error import HTTPError, URLError

from django.test import SimpleTestCase, override_settings

from api.services.interscity import ClienteInterSCity


class ClienteInterSCityTests(SimpleTestCase):
    @override_settings(
        INTERSCITY_ENABLED=True,
        INTERSCITY_BASE_URL="http://interscity.example",
        INTERSCITY_ADAPTOR_PATH="/adaptor",
    )
    @patch("api.services.interscity.urlopen")
    def test_publicar_dados_recurso_envia_para_resource_adaptor(self, urlopen):
        cliente = ClienteInterSCity()

        ok = cliente.publicar_dados_recurso(
            "resource-uuid",
            "autoponto_device_status",
            {"status": "online", "date": "2026-04-20T10:00:00Z"},
        )

        self.assertTrue(ok)
        requisicao = urlopen.call_args.args[0]
        self.assertEqual(requisicao.full_url, "http://interscity.example/adaptor/resources/resource-uuid/data")
        self.assertEqual(requisicao.get_method(), "POST")
        self.assertIn(b"autoponto_device_status", requisicao.data)
        self.assertIn(b"online", requisicao.data)

    @override_settings(
        INTERSCITY_ENABLED=True,
        INTERSCITY_BASE_URL="http://interscity.example",
        INTERSCITY_ADAPTOR_PATH="/adaptor",
    )
    @patch("api.services.interscity.urlopen", side_effect=URLError("offline"))
    def test_publicar_dados_recurso_retorna_false_quando_interscity_indisponivel(self, urlopen):
        cliente = ClienteInterSCity()

        ok = cliente.publicar_dados_recurso(
            "resource-uuid",
            "autoponto_device_status",
            {"status": "online", "date": "2026-04-20T10:00:00Z"},
        )

        self.assertFalse(ok)

    @override_settings(
        INTERSCITY_ENABLED=True,
        INTERSCITY_BASE_URL="http://interscity.example",
        INTERSCITY_CATALOG_PATH="/catalog",
    )
    @patch("api.services.interscity.urlopen")
    def test_registrar_recurso_catalogo_usa_resource_cataloguer(self, urlopen):
        cliente = ClienteInterSCity()

        ok = cliente.registrar_recurso_catalogo(
            {
                "uuid": "resource-uuid",
                "description": "ESP32 Sala 101",
                "capabilities": ["autoponto_device_status"],
            }
        )

        self.assertTrue(ok)
        requisicao = urlopen.call_args.args[0]
        self.assertEqual(requisicao.full_url, "http://interscity.example/catalog/resources")
        self.assertEqual(requisicao.get_method(), "POST")
        self.assertIn(b"autoponto_device_status", requisicao.data)

    @override_settings(INTERSCITY_ENABLED=False)
    @patch("api.services.interscity.urlopen")
    def test_cliente_desabilitado_nao_chama_http(self, urlopen):
        cliente = ClienteInterSCity()

        ok = cliente.publicar_dados_recurso("uuid", "autoponto_device_status", {"status": "online"})

        self.assertFalse(ok)
        urlopen.assert_not_called()

    @override_settings(
        INTERSCITY_ENABLED=True,
        INTERSCITY_BASE_URL="http://interscity.example",
        INTERSCITY_CATALOG_PATH="/catalog",
        INTERSCITY_DISCOVERY_PATH="/discovery",
        INTERSCITY_COLLECTOR_PATH="/collector",
        INTERSCITY_ADAPTOR_PATH="/adaptor",
        INTERSCITY_ACTUATOR_PATH="/actuator",
    )
    @patch("api.services.interscity.urlopen")
    def test_diagnostico_retorna_status_individual_para_todos_os_microsservicos(self, urlopen):
        urlopen.side_effect = [
            object(),
            timeout("demorou"),
            HTTPError("http://collector", 500, "erro", {}, None),
            URLError("offline"),
            object(),
        ]
        cliente = ClienteInterSCity()

        diagnostico = cliente.diagnosticar_servicos()

        self.assertEqual(diagnostico["catalog"]["status"], "ok")
        self.assertEqual(diagnostico["discovery"]["status"], "timeout")
        self.assertEqual(diagnostico["collector"]["status"], "erro_http")
        self.assertEqual(diagnostico["adaptor"]["status"], "indisponivel")
        self.assertEqual(diagnostico["actuator"]["status"], "ok")
