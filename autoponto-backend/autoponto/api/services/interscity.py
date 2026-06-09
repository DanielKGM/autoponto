import json
from socket import timeout as SocketTimeout
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings


STATUS_OK = "ok"
STATUS_TIMEOUT = "timeout"
STATUS_ERRO_HTTP = "erro_http"
STATUS_INDISPONIVEL = "indisponivel"
STATUS_NAO_CONFIGURADO = "nao_configurado"


class ClienteInterSCity:
    def __init__(self, timeout: int | None = None):
        self.base_url = settings.INTERSCITY_BASE_URL.rstrip("/")
        self.catalog_url = self._url_servico(settings.INTERSCITY_CATALOG_PATH)
        self.adaptor_url = self._url_servico(settings.INTERSCITY_ADAPTOR_PATH)
        self.collector_url = self._url_servico(settings.INTERSCITY_COLLECTOR_PATH)
        self.discovery_url = self._url_servico(settings.INTERSCITY_DISCOVERY_PATH)
        self.actuator_url = self._url_servico(settings.INTERSCITY_ACTUATOR_PATH)
        self.timeout = timeout if timeout is not None else settings.INTERSCITY_TIMEOUT_SECONDS

    def _url_servico(self, caminho: str) -> str:
        return f"{self.base_url}/{caminho.strip('/')}".rstrip("/")

    def _habilitado(self, base_url: str) -> bool:
        return bool(settings.INTERSCITY_ENABLED and base_url)

    def _request_status(self, metodo: str, base_url: str, caminho: str, corpo: dict | None = None) -> dict:
        if not self._habilitado(base_url):
            return {"ok": False, "status": STATUS_NAO_CONFIGURADO, "detalhe": "Integracao desabilitada ou URL ausente."}

        dados = json.dumps(corpo or {}).encode("utf-8") if corpo is not None else None
        requisicao = Request(
            f"{base_url}{caminho}",
            data=dados,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method=metodo,
        )
        resposta = None
        try:
            resposta = urlopen(requisicao, timeout=self.timeout)
            return {"ok": True, "status": STATUS_OK, "codigo_http": getattr(resposta, "status", None)}
        except (TimeoutError, SocketTimeout):
            return {"ok": False, "status": STATUS_TIMEOUT, "detalhe": "Tempo limite excedido."}
        except HTTPError as exc:
            return {
                "ok": False,
                "status": STATUS_ERRO_HTTP,
                "codigo_http": exc.code,
                "detalhe": str(exc.reason),
            }
        except URLError as exc:
            return {"ok": False, "status": STATUS_INDISPONIVEL, "detalhe": str(exc.reason)}
        except OSError as exc:
            return {"ok": False, "status": STATUS_INDISPONIVEL, "detalhe": str(exc)}
        finally:
            if resposta and hasattr(resposta, "close"):
                resposta.close()

    def _request(self, metodo: str, base_url: str, caminho: str, corpo: dict | None = None) -> bool:
        return self._request_status(metodo, base_url, caminho, corpo)["ok"]

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

    def diagnosticar_servicos(self) -> dict:
        servicos = {
            "catalog": (self.catalog_url, "/"),
            "discovery": (self.discovery_url, "/"),
            "collector": (self.collector_url, "/"),
            "adaptor": (self.adaptor_url, "/"),
            "actuator": (self.actuator_url, "/"),
        }
        return {
            nome: self._request_status("GET", base_url, caminho)
            for nome, (base_url, caminho) in servicos.items()
        }

    publish_resource_data = publicar_dados_recurso


InterSCityClient = ClienteInterSCity
