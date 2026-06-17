from socket import timeout
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from django.test import SimpleTestCase, override_settings

from api.services.interscity import ClienteInterSCity


class ClienteInterSCityTests(SimpleTestCase):
    @override_settings(INTERSCITY_ENABLED=False)
    @patch("api.services.interscity.urlopen")
    def test_cliente_desabilitado_nao_chama_http(self, urlopen):
        cliente = ClienteInterSCity()

        diagnostico = cliente.diagnosticar_servicos()

        self.assertEqual(diagnostico["catalog"]["status"], "nao_configurado")
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
