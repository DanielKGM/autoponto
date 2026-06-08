import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


class ClienteInterSCity:
    def __init__(self, timeout: int | None = None):
        self.catalog_url = settings.INTERSCITY_CATALOG_URL.rstrip("/")
        self.adaptor_url = settings.INTERSCITY_ADAPTOR_URL.rstrip("/")
        self.collector_url = settings.INTERSCITY_COLLECTOR_URL.rstrip("/")
        self.discovery_url = settings.INTERSCITY_DISCOVERY_URL.rstrip("/")
        self.actuator_url = settings.INTERSCITY_ACTUATOR_URL.rstrip("/")
        self.timeout = timeout if timeout is not None else settings.INTERSCITY_TIMEOUT_SECONDS

    def _habilitado(self, base_url: str) -> bool:
        return bool(settings.INTERSCITY_ENABLED and base_url)

    def _request(self, metodo: str, base_url: str, caminho: str, corpo: dict | None = None) -> bool:
        if not self._habilitado(base_url):
            return False

        dados = json.dumps(corpo or {}).encode("utf-8") if corpo is not None else None
        requisicao = Request(
            f"{base_url}{caminho}",
            data=dados,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method=metodo,
        )
        try:
            with urlopen(requisicao, timeout=self.timeout):
                return True
        except URLError:
            return False

    def registrar_recurso_catalogo(self, recurso: dict) -> bool:
        return self._request("POST", self.catalog_url, "/resources", recurso)

    def publicar_dados_recurso(self, uuid_recurso: str, capacidade: str, valor: dict) -> bool:
        corpo = {"data": {capacidade: [valor]}}
        return self._request("POST", self.adaptor_url, f"/resources/{uuid_recurso}/data", corpo)

    def consultar_dados_coletor(self, uuid_recurso: str, capacidade: str) -> bool:
        caminho = f"/resources/{uuid_recurso}/data?{urlencode({'capability': capacidade})}"
        return self._request("GET", self.collector_url, caminho)

    def descobrir_recursos(self, filtros: dict) -> bool:
        caminho = f"/resources?{urlencode(filtros, doseq=True)}"
        return self._request("GET", self.discovery_url, caminho)

    def enviar_comando_atuador(self, uuid_recurso: str, capacidade: str, valor: dict) -> bool:
        corpo = {"capability": capacidade, "value": valor}
        return self._request("POST", self.actuator_url, f"/resources/{uuid_recurso}/commands", corpo)

    publish_resource_data = publicar_dados_recurso


InterSCityClient = ClienteInterSCity
