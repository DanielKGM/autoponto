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

CAP_DEVICE_STATUS = "autoponto_device_status"
CAP_CLASS_CONTEXT = "autoponto_class_context"
CAP_ATTENDANCE_EVENT = "autoponto_attendance_event"
CAPACIDADES_DISPOSITIVO = [CAP_DEVICE_STATUS, CAP_CLASS_CONTEXT, CAP_ATTENDANCE_EVENT]


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

    def _request_json(self, metodo: str, base_url: str, caminho: str, corpo: dict | None = None) -> dict:
        if not self._habilitado(base_url):
            return {"ok": False, "status": STATUS_NAO_CONFIGURADO, "data": None}

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
            corpo_resposta = b""
            if hasattr(resposta, "read"):
                corpo_resposta = resposta.read() or b""
            data = json.loads(corpo_resposta.decode("utf-8")) if corpo_resposta else None
            return {"ok": True, "status": STATUS_OK, "codigo_http": getattr(resposta, "status", None), "data": data}
        except (TimeoutError, SocketTimeout):
            return {"ok": False, "status": STATUS_TIMEOUT, "detalhe": "Tempo limite excedido.", "data": None}
        except HTTPError as exc:
            return {"ok": False, "status": STATUS_ERRO_HTTP, "codigo_http": exc.code, "detalhe": str(exc.reason), "data": None}
        except URLError as exc:
            return {"ok": False, "status": STATUS_INDISPONIVEL, "detalhe": str(exc.reason), "data": None}
        except (OSError, ValueError) as exc:
            return {"ok": False, "status": STATUS_INDISPONIVEL, "detalhe": str(exc), "data": None}
        finally:
            if resposta and hasattr(resposta, "close"):
                resposta.close()

    def _request(self, metodo: str, base_url: str, caminho: str, corpo: dict | None = None) -> bool:
        return self._request_status(metodo, base_url, caminho, corpo)["ok"]

    def registrar_recurso_catalogo(self, recurso: dict) -> bool:
        return self._request("POST", self.catalog_url, "/resources", recurso)

    def registrar_ou_atualizar_recurso_catalogo(self, recurso: dict, uuid_recurso: str = "") -> dict:
        if uuid_recurso:
            return self._request_json("PUT", self.catalog_url, f"/resources/{uuid_recurso}", recurso)
        return self._request_json("POST", self.catalog_url, "/resources", recurso)

    def publicar_dados_recurso(self, uuid_recurso: str, capacidade: str, valor: dict) -> bool:
        corpo = {"data": {capacidade: [valor]}}
        return self._request("POST", self.adaptor_url, f"/resources/{uuid_recurso}/data", corpo)

    def consultar_dados_coletor(self, uuid_recurso: str, capacidade: str) -> bool:
        caminho = f"/resources/{uuid_recurso}/data?{urlencode({'capability': capacidade})}"
        return self._request("GET", self.collector_url, caminho)

    def consultar_ultimo_dado_recurso(self, uuid_recurso: str, capacidade: str) -> dict:
        return self._request_json(
            "POST",
            self.collector_url,
            f"/resources/{uuid_recurso}/data/last",
            {"capabilities": [capacidade]},
        )

    def descobrir_recursos(self, filtros: dict) -> bool:
        caminho = f"/resources?{urlencode(filtros, doseq=True)}"
        return self._request("GET", self.discovery_url, caminho)

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


def _extrair_uuid_recurso(resposta: dict) -> str:
    data = resposta.get("data")
    if not isinstance(data, dict):
        return ""
    candidatos = [
        data.get("uuid"),
        data.get("id"),
        data.get("data", {}).get("uuid") if isinstance(data.get("data"), dict) else "",
        data.get("resource", {}).get("uuid") if isinstance(data.get("resource"), dict) else "",
    ]
    return next((str(valor) for valor in candidatos if valor), "")


def payload_recurso_dispositivo(dispositivo) -> dict:
    sala = dispositivo.sala
    predio = sala.predio if sala else None
    descricao = f"AutoPonto ESP32 {dispositivo.codigo}"
    if sala:
        descricao = f"{descricao} - {sala.nome}"
    return {
        "data": {
            "uri": f"autoponto://dispositivos-esp32/{dispositivo.id}",
            "description": descricao,
            "status": "active" if dispositivo.ativo else "inactive",
            "capabilities": CAPACIDADES_DISPOSITIVO,
            "metadata": {
                "autoponto_id": str(dispositivo.id),
                "codigo": dispositivo.codigo,
                "sala": sala.nome if sala else "",
                "predio": predio.nome if predio else "",
                "no": dispositivo.no.codigo if dispositivo.no else "",
            },
        }
    }


def publicar_status_dispositivo_interscity(dispositivo, *, reportado_em, origem: str = "edge_mqtt") -> bool:
    if not getattr(settings, "INTERSCITY_ENABLED", False) or not dispositivo.interscity_uuid:
        return False
    valor = {
        "status": dispositivo.status,
        "device_id": str(dispositivo.id),
        "node_id": dispositivo.no.codigo if dispositivo.no else "",
        "timestamp": reportado_em.isoformat().replace("+00:00", "Z"),
        "source": origem,
    }
    return ClienteInterSCity().publicar_dados_recurso(dispositivo.interscity_uuid, CAP_DEVICE_STATUS, valor)


def sincronizar_recursos_iot_interscity() -> dict:
    from api.models import DispositivoEsp32

    cliente = ClienteInterSCity()
    sincronizados = []
    falhas = []
    dispositivos = DispositivoEsp32.objects.select_related("sala", "sala__predio", "no").filter(ativo=True)
    for dispositivo in dispositivos:
        resposta = cliente.registrar_ou_atualizar_recurso_catalogo(
            payload_recurso_dispositivo(dispositivo),
            uuid_recurso=dispositivo.interscity_uuid,
        )
        if not resposta.get("ok"):
            falhas.append({"id": str(dispositivo.id), "status": resposta.get("status")})
            continue
        uuid_recurso = dispositivo.interscity_uuid or _extrair_uuid_recurso(resposta)
        if uuid_recurso and uuid_recurso != dispositivo.interscity_uuid:
            dispositivo.interscity_uuid = uuid_recurso
            dispositivo.save(update_fields=["interscity_uuid", "atualizado_em"])
        sincronizados.append({"id": str(dispositivo.id), "uuid": dispositivo.interscity_uuid})
    return {"sincronizados": sincronizados, "falhas": falhas}


def consultar_status_interscity(dispositivo) -> dict:
    if not dispositivo.interscity_uuid:
        return {"ok": False, "status": STATUS_NAO_CONFIGURADO, "data": None}
    return ClienteInterSCity().consultar_ultimo_dado_recurso(dispositivo.interscity_uuid, CAP_DEVICE_STATUS)
