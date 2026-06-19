import json
from socket import timeout as SocketTimeout
from urllib.error import HTTPError, URLError
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
        self.timeout = (
            timeout if timeout is not None else settings.INTERSCITY_TIMEOUT_SECONDS
        )

    def _url_servico(self, caminho: str) -> str:
        return f"{self.base_url}/{caminho.strip('/')}".rstrip("/")

    def _request_status(
        self, metodo: str, base_url: str, caminho: str, corpo: dict | None = None
    ) -> dict:
        if not settings.INTERSCITY_ENABLED or not base_url:
            return {
                "ok": False,
                "status": STATUS_NAO_CONFIGURADO,
                "detalhe": "Integracao desabilitada ou URL ausente.",
            }

        dados = json.dumps(corpo or {}).encode("utf-8") if corpo is not None else None
        headers = {"Accept": "*/*"}
        if dados is not None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        requisicao = Request(
            f"{base_url}{caminho}",
            data=dados,
            headers=headers,
            method=metodo,
        )
        resposta = None
        try:
            resposta = urlopen(requisicao, timeout=self.timeout)
            return {
                "ok": True,
                "status": STATUS_OK,
                "codigo_http": getattr(resposta, "status", None),
            }
        except (TimeoutError, SocketTimeout):
            return {
                "ok": False,
                "status": STATUS_TIMEOUT,
                "detalhe": "Tempo limite excedido.",
            }
        except HTTPError as exc:
            return {
                "ok": False,
                "status": STATUS_ERRO_HTTP,
                "codigo_http": exc.code,
                "detalhe": str(exc.reason),
            }
        except URLError as exc:
            return {
                "ok": False,
                "status": STATUS_INDISPONIVEL,
                "detalhe": str(exc.reason),
            }
        except OSError as exc:
            return {"ok": False, "status": STATUS_INDISPONIVEL, "detalhe": str(exc)}
        finally:
            if resposta and hasattr(resposta, "close"):
                resposta.close()

    def _request_json(
        self, metodo: str, base_url: str, caminho: str, corpo: dict | None = None
    ) -> dict:
        if not settings.INTERSCITY_ENABLED or not base_url:
            return {
                "ok": False,
                "status": STATUS_NAO_CONFIGURADO,
                "detalhe": "Integracao desabilitada ou URL ausente.",
                "data": {},
            }

        dados = json.dumps(corpo or {}).encode("utf-8") if corpo is not None else None
        headers = {"Accept": "*/*"}
        if dados is not None:
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
        requisicao = Request(
            f"{base_url}{caminho}",
            data=dados,
            headers=headers,
            method=metodo,
        )
        resposta = None
        try:
            resposta = urlopen(requisicao, timeout=self.timeout)
            conteudo = (
                resposta.read().decode("utf-8") if hasattr(resposta, "read") else "{}"
            )
            return {
                "ok": True,
                "status": STATUS_OK,
                "codigo_http": getattr(resposta, "status", None),
                "data": json.loads(conteudo or "{}"),
            }
        except (TimeoutError, SocketTimeout):
            return {
                "ok": False,
                "status": STATUS_TIMEOUT,
                "detalhe": "Tempo limite excedido.",
                "data": {},
            }
        except HTTPError as exc:
            return {
                "ok": False,
                "status": STATUS_ERRO_HTTP,
                "codigo_http": exc.code,
                "detalhe": str(exc.reason),
                "data": {},
            }
        except URLError as exc:
            return {
                "ok": False,
                "status": STATUS_INDISPONIVEL,
                "detalhe": str(exc.reason),
                "data": {},
            }
        except (OSError, ValueError) as exc:
            return {
                "ok": False,
                "status": STATUS_INDISPONIVEL,
                "detalhe": str(exc),
                "data": {},
            }
        finally:
            if resposta and hasattr(resposta, "close"):
                resposta.close()

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

    def buscar_historico_recursos(
        self,
        *,
        uuids: list[str],
        capabilities: list[str],
        start_date: str,
        end_date: str,
    ) -> dict:
        corpo = {
            "uuids": uuids,
            "capabilities": capabilities,
            "start_date": start_date,
            "end_date": end_date,
        }
        resposta = self._request_json(
            "POST", self.collector_url, "/resources/data", corpo
        )
        return {
            "ok": resposta["ok"],
            "status": resposta["status"],
            "resources": resposta.get("data", {}).get("resources", []),
            "detalhe": resposta.get("detalhe"),
        }
