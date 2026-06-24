from datetime import datetime, timedelta, timezone as datetime_timezone

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import DispositivoEsp32, NoBorda
from api.services.interscity import ClienteInterSCity

CAPACIDADES_MAPA = [
    "status",
    "presenca",
    "lesson",
    "now_ms",
    "next_ms",
    "remaining_ms",
    "heap_free",
    "heap_min",
    "heap_max",
    "psram_free",
    "psram_min",
    "psram_max",
    "rssi",
    "post_max_ms",
]


def _iso(valor):
    return valor.isoformat().replace("+00:00", "Z")


def _data_capacidade(item: dict):
    data = item.get("date") or ""
    try:
        return datetime.fromisoformat(str(data).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def _valor_bool(valor):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return valor != 0
    if isinstance(valor, str):
        normalizado = valor.strip().lower()
        if normalizado in {"true", "1", "sim", "yes", "on"}:
            return True
        if normalizado in {"false", "0", "nao", "no", "off"}:
            return False
    return None


def _normalizar_data(valor):
    if not valor:
        return None
    try:
        data = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except ValueError:
        return None
    if timezone.is_naive(data):
        return timezone.make_aware(data, datetime_timezone.utc)
    return data


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
        "interscity_uuid": dispositivo.interscity_uuid,
    }


def _payload_no(no: NoBorda) -> dict:
    return {
        "id": str(no.id),
        "codigo": no.codigo,
        "nome": no.nome,
        "latitude": _coordenada(no.latitude),
        "longitude": _coordenada(no.longitude),
        "ultimo_sync_em": _iso(no.ultimo_sync_em) if no.ultimo_sync_em else None,
        "dispositivos": [
            _payload_dispositivo(dispositivo) for dispositivo in no.dispositivos.all()
        ],
    }


def _queryset_nos_mapa():
    dispositivos_ativos = (
        DispositivoEsp32.objects.select_related("sala", "sala__predio")
        .filter(ativo=True)
        .order_by("codigo")
    )
    return (
        NoBorda.objects.filter(
            ativo=True,
            latitude__isnull=False,
            longitude__isnull=False,
        )
        .prefetch_related(Prefetch("dispositivos", queryset=dispositivos_ativos))
        .order_by("codigo")
    )


def _queryset_dispositivos_historico():
    return (
        DispositivoEsp32.objects.select_related("sala", "sala__predio", "no")
        .filter(
            ativo=True,
            interscity_uuid__gt="",
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


def _buscar_telemetria_dispositivo(
    request,
    dispositivo: DispositivoEsp32,
) -> tuple[dict, str, datetime | None, datetime | None]:
    periodo = (request.query_params.get("periodo") or "").strip().lower()
    cliente = ClienteInterSCity()
    if periodo in {"recentes", "recente", "ultimo", "ultimos", "last"}:
        return (
            cliente.buscar_ultimos_recursos(uuids=[dispositivo.interscity_uuid]),
            "recentes",
            None,
            None,
        )

    fim = timezone.now()
    if periodo in {"2h", "duas_horas", "ultimas_2h", "ultimas_duas_horas"}:
        inicio = fim - timedelta(hours=2)
        periodo_resolvido = "2h"
    elif periodo in {"1h", "hora", "ultima_hora"}:
        inicio = fim - timedelta(hours=2)
        periodo_resolvido = "2h"
    else:
        try:
            dias = int(
                request.query_params.get("dias", 1 if periodo == "1d" else 7)
            )
        except ValueError:
            dias = 7
        dias = max(1, min(dias, 7))
        inicio = fim - timedelta(days=dias)
        periodo_resolvido = "1d" if dias == 1 else f"{dias}d"

    return (
        cliente.buscar_historico_recursos(
            uuids=[dispositivo.interscity_uuid],
            capabilities=CAPACIDADES_MAPA,
            start_date=_iso(inicio),
            end_date=_iso(fim),
        ),
        periodo_resolvido,
        inicio,
        fim,
    )


def _payload_pir(
    historico: dict,
    periodo: str,
    inicio_periodo: datetime | None = None,
    fim_periodo: datetime | None = None,
) -> dict:
    amostras = []
    for item in historico.get("presenca", []):
        data = _normalizar_data(item.get("date"))
        valor = _valor_bool(item.get("value"))
        if data is None or valor is None:
            continue
        amostras.append(
            {
                "timestamp": _iso(data),
                "valor": valor,
                "nivel": 1 if valor else 0,
            }
        )

    if periodo == "1d":
        baldes = []
        if amostras:
            inicio_base = inicio_periodo or _normalizar_data(amostras[0]["timestamp"])
            fim_base = fim_periodo or _normalizar_data(amostras[-1]["timestamp"])
            inicio = inicio_base.replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            fim = fim_base.replace(
                minute=0,
                second=0,
                microsecond=0,
            )
            cursor = inicio
            while cursor <= fim:
                proximo = cursor + timedelta(hours=1)
                quantidade = sum(
                    1
                    for amostra in amostras
                    if amostra["valor"]
                    and cursor
                    <= _normalizar_data(amostra["timestamp"])
                    < proximo
                )
                baldes.append(
                    {
                        "inicio": _iso(cursor),
                        "fim": _iso(proximo),
                        "quantidade": quantidade,
                    }
                )
                cursor = proximo
        return {
            "tipo": "histograma",
            "balde_minutos": 60,
            "eventos": amostras,
            "baldes": baldes,
            "total": sum(1 for amostra in amostras if amostra["valor"]),
        }

    return {
        "tipo": "linha_tempo",
        "eventos": amostras,
        "baldes": [],
        "total": sum(1 for amostra in amostras if amostra["valor"]),
    }


class MapaNosPublicosView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response([_payload_no(no) for no in _queryset_nos_mapa()])


class MapaDispositivosPublicosView(MapaNosPublicosView):
    pass


class MapaDispositivoHistoricoView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, dispositivo_id):
        dispositivo = get_object_or_404(
            _queryset_dispositivos_historico(), id=dispositivo_id
        )
        resultado, periodo, inicio, fim = _buscar_telemetria_dispositivo(
            request,
            dispositivo,
        )
        historico = _filtrar_capacidades(
            resultado.get("resources", []), dispositivo.interscity_uuid
        )
        return Response(
            {
                "dispositivo": _payload_dispositivo(dispositivo),
                "collector_status": resultado["status"],
                "periodo": periodo,
                "historico": historico,
                "pir": _payload_pir(historico, periodo, inicio, fim),
                "ultimo": {
                    nome: valores[-1] for nome, valores in historico.items() if valores
                },
            }
        )
