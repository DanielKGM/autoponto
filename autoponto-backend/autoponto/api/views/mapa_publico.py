from datetime import datetime, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import DispositivoEsp32
from api.services.interscity import ClienteInterSCity

CAPACIDADES_MAPA = [
    "now_ms",
    "next_ms",
    "remaining_ms",
    "heap_free",
    "psram_free",
    "lesson",
    "heap_min",
    "rssi",
    "status",
    "presenca",
]


def _iso(valor):
    return valor.isoformat().replace("+00:00", "Z")


def _data_capacidade(item: dict):
    data = item.get("date") or ""
    try:
        return datetime.fromisoformat(str(data).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def _coordenada(valor):
    if valor is None:
        return None
    return f"{valor:.6f}"


def _payload_dispositivo(dispositivo: DispositivoEsp32) -> dict:
    sala = dispositivo.sala
    predio = sala.predio if sala else None
    return {
        "id": str(dispositivo.id),
        "codigo": dispositivo.codigo,
        "nome": dispositivo.nome,
        "sala": sala.nome if sala else None,
        "predio": predio.nome if predio else None,
        "latitude": _coordenada(dispositivo.latitude),
        "longitude": _coordenada(dispositivo.longitude),
        "interscity_uuid": dispositivo.interscity_uuid,
    }


def _queryset_mapa():
    return (
        DispositivoEsp32.objects.select_related("sala", "sala__predio")
        .filter(
            ativo=True,
            interscity_uuid__gt="",
            latitude__isnull=False,
            longitude__isnull=False,
        )
        .order_by("codigo")
    )


def _filtrar_capacidades(resources: list[dict], interscity_uuid: str) -> dict:
    for resource in resources:
        if resource.get("uuid") != interscity_uuid:
            continue
        capabilities = resource.get("capabilities") or {}
        historico = {}
        for nome in CAPACIDADES_MAPA:
            valores = capabilities.get(nome)
            if not isinstance(valores, list):
                continue
            historico[nome] = sorted(valores, key=_data_capacidade)
        return historico
    return {}


def _ultimos_valores(historico: dict) -> dict:
    ultimos = {}
    for nome, valores in historico.items():
        if valores:
            ultimos[nome] = valores[-1]
    return ultimos


class MapaDispositivosPublicosView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(
            [_payload_dispositivo(dispositivo) for dispositivo in _queryset_mapa()]
        )


class MapaDispositivoHistoricoView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, dispositivo_id):
        dispositivo = get_object_or_404(_queryset_mapa(), id=dispositivo_id)
        try:
            dias = int(request.query_params.get("dias", 7))
        except ValueError:
            dias = 7
        dias = max(1, min(dias, 7))
        fim = timezone.now()
        inicio = fim - timedelta(days=dias)

        resultado = ClienteInterSCity().buscar_historico_recursos(
            uuids=[dispositivo.interscity_uuid],
            capabilities=CAPACIDADES_MAPA,
            start_date=_iso(inicio),
            end_date=_iso(fim),
        )
        historico = _filtrar_capacidades(
            resultado.get("resources", []), dispositivo.interscity_uuid
        )
        return Response(
            {
                "dispositivo": _payload_dispositivo(dispositivo),
                "collector_status": resultado["status"],
                "historico": historico,
                "ultimo": _ultimos_valores(historico),
            }
        )
