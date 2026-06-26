from django.db.models import Case, CharField, DateTimeField, QuerySet, Value, When
from django.db.models.functions import Now
from django.utils import timezone

from api.models import Aula


STATUS_AULA_VALIDOS = {valor for valor, _ in Aula.STATUS_CHOICES}


def status_aula_expression(agora=None):
    agora_expr = Now() if agora is None else Value(agora, output_field=DateTimeField())
    return Case(
        When(cancelada_em__isnull=False, then=Value(Aula.STATUS_CANCELADA)),
        When(fechada_em__isnull=False, then=Value(Aula.STATUS_FECHADA)),
        When(fim__lte=agora_expr, then=Value(Aula.STATUS_FECHADA)),
        When(inicio__lte=agora_expr, fim__gt=agora_expr, then=Value(Aula.STATUS_ABERTA)),
        default=Value(Aula.STATUS_PLANEJADA),
        output_field=CharField(),
    )


def com_status_aula(queryset: QuerySet | None = None, agora=None) -> QuerySet:
    queryset = queryset if queryset is not None else Aula.objects.all()
    return queryset.annotate(status=status_aula_expression(agora=agora))


def filtrar_status_aula(queryset: QuerySet, status: str | None, agora=None) -> QuerySet:
    if not status:
        return com_status_aula(queryset, agora=agora)
    return com_status_aula(queryset, agora=agora).filter(status=status)


def status_aula(aula: Aula, agora=None) -> str:
    anotado = getattr(aula, "status", None)
    if anotado in STATUS_AULA_VALIDOS:
        return anotado

    agora = agora or timezone.now()
    if aula.cancelada_em:
        return Aula.STATUS_CANCELADA
    if aula.fechada_em:
        return Aula.STATUS_FECHADA
    if aula.fim <= agora:
        return Aula.STATUS_FECHADA
    if aula.inicio <= agora < aula.fim:
        return Aula.STATUS_ABERTA
    return Aula.STATUS_PLANEJADA
