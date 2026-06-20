from django.conf import settings

from api.models import EventoSincronizacaoBorda


def registrar_evento_sync(entidade: str, acao: str, identificador) -> EventoSincronizacaoBorda:
    evento = EventoSincronizacaoBorda.objects.create(
        entidade=entidade,
        acao=acao,
        identificador=identificador,
    )
    aplicar_retencao_eventos_sync()
    return evento


def aplicar_retencao_eventos_sync() -> None:
    limite = int(getattr(settings, "EDGE_AUDIT_MAX_EVENTS", 100000))
    if limite <= 0:
        return

    excedente = EventoSincronizacaoBorda.objects.count() - limite
    if excedente <= 0:
        return

    ids_antigos = list(
        EventoSincronizacaoBorda.objects.order_by("id").values_list("id", flat=True)[
            :excedente
        ]
    )
    EventoSincronizacaoBorda.objects.filter(id__in=ids_antigos).delete()
