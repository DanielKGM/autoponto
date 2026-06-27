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
        self.collector_url = self._url_servico(settings.INTERSCITY_COLLECTOR_PATH)
        self.timeout = (
            timeout if timeout is not None else settings.INTERSCITY_TIMEOUT_SECONDS
        )

    def _url_servico(self, caminho: str) -> str:
        return f"{self.base_url}/{caminho.strip('/')}".rstrip("/")

    def _request_status(
        self, metodo: str, base_url: str, caminho: str, corpo: dict | None = None
    ) -> dict:

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
        return {"collector": self._request_status("GET", self.collector_url, "/")}

    def _resources_da_resposta(self, resposta: dict) -> list[dict]:
        dados = resposta.get("data", {})
        if not isinstance(dados, dict):
            return []
        resources = dados.get("resources")
        if isinstance(resources, list):
            return resources
        response_content = dados.get("response_content")
        if isinstance(response_content, dict):
            resources = response_content.get("resources")
            if isinstance(resources, list):
                return resources
        return []

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
            "resources": self._resources_da_resposta(resposta),
            "detalhe": resposta.get("detalhe"),
        }

    def buscar_ultimos_recursos(self, *, uuids: list[str]) -> dict:
        resposta = self._request_json(
            "POST", self.collector_url, "/resources/data/last", {"uuids": uuids}
        )
        return {
            "ok": resposta["ok"],
            "status": resposta["status"],
            "resources": self._resources_da_resposta(resposta),
            "detalhe": resposta.get("detalhe"),
        }
