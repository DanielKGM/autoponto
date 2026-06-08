from unittest.mock import patch
from urllib.error import URLError

from django.test import SimpleTestCase, override_settings

from api.services.interscity import ClienteInterSCity


class ClienteInterSCityTests(SimpleTestCase):
    @override_settings(INTERSCITY_ENABLED=True, INTERSCITY_ADAPTOR_URL="http://interscity.example/adaptor")
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

    @override_settings(INTERSCITY_ENABLED=True, INTERSCITY_ADAPTOR_URL="http://interscity.example/adaptor")
    @patch("api.services.interscity.urlopen", side_effect=URLError("offline"))
    def test_publicar_dados_recurso_retorna_false_quando_interscity_indisponivel(self, urlopen):
        cliente = ClienteInterSCity()

        ok = cliente.publicar_dados_recurso(
            "resource-uuid",
            "autoponto_device_status",
            {"status": "online", "date": "2026-04-20T10:00:00Z"},
        )

        self.assertFalse(ok)

    @override_settings(INTERSCITY_ENABLED=True, INTERSCITY_CATALOG_URL="http://interscity.example/catalog")
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
