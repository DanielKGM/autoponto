from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from api.models import Aula, HorarioPadraoUFMA, Sala, Turma
from .errors import DomainValidationError


def calcular_intervalo_aula(horario_padrao: HorarioPadraoUFMA, data_aula):
    inicio = timezone.make_aware(datetime.combine(data_aula, horario_padrao.horario_inicio))
    fim = timezone.make_aware(datetime.combine(data_aula, horario_padrao.horario_fim))
    return inicio, fim


def _datas_do_horario(turma: Turma, horario_padrao: HorarioPadraoUFMA):
    atual = turma.periodo_letivo.data_inicio
    fim = turma.periodo_letivo.data_fim
    while atual <= fim:
        if atual.weekday() == horario_padrao.weekday_python:
            yield atual
        atual += timedelta(days=1)


def _normalizar_horarios(horarios: list[dict]) -> set[tuple[object, object]]:
    pares = set()
    for item in horarios:
        sala = item["sala"]
        horario_padrao = item["horario_padrao"]
        sala_id = getattr(sala, "id", sala)
        horario_padrao_id = getattr(horario_padrao, "id", horario_padrao)
        pares.add((sala_id, horario_padrao_id))
    return pares


def _validar_horarios_obrigatorios(turma: Turma, horarios: list[dict]) -> None:
    if turma.ativo and not horarios:
        raise DomainValidationError("Turma ativa deve possuir ao menos um horario.")


def _validar_conflito_sala(turma: Turma, sala: Sala, horario_padrao: HorarioPadraoUFMA) -> None:
    conflito = Aula.objects.filter(
        turma__periodo_letivo=turma.periodo_letivo,
        sala=sala,
        horario_padrao__dia_semana=horario_padrao.dia_semana,
        horario_padrao__horario_inicio__lt=horario_padrao.horario_fim,
        horario_padrao__horario_fim__gt=horario_padrao.horario_inicio,
    ).exclude(turma=turma).exclude(status=Aula.STATUS_CANCELADA)
    if conflito.exists():
        raise DomainValidationError("Ja existe aula nessa sala no periodo, dia e horario informados.")


def _criar_ou_atualizar_aulas(turma: Turma, horarios: list[dict]) -> None:
    for item in horarios:
        sala = item["sala"]
        horario_padrao = item["horario_padrao"]
        _validar_conflito_sala(turma, sala, horario_padrao)
        for data_aula in _datas_do_horario(turma, horario_padrao):
            inicio, fim = calcular_intervalo_aula(horario_padrao, data_aula)
            aula, criada = Aula.objects.get_or_create(
                turma=turma,
                horario_padrao=horario_padrao,
                data=data_aula,
                defaults={
                    "sala": sala,
                    "inicio": inicio,
                    "fim": fim,
                    "status": Aula.STATUS_PLANEJADA,
                },
            )
            if not criada and not aula.presencas.exists() and aula.status != Aula.STATUS_FECHADA:
                aula.sala = sala
                aula.inicio = inicio
                aula.fim = fim
                if aula.status == Aula.STATUS_CANCELADA:
                    aula.status = Aula.STATUS_PLANEJADA
                aula.save(update_fields=["sala", "inicio", "fim", "status", "atualizado_em"])


def _cancelar_aulas_futuras_removidas(turma: Turma, pares_desejados: set[tuple[object, object]]) -> None:
    hoje = timezone.localdate()
    aulas = Aula.objects.filter(turma=turma, data__gte=hoje).exclude(status=Aula.STATUS_CANCELADA)
    for aula in aulas:
        par = (aula.sala_id, aula.horario_padrao_id)
        if par in pares_desejados:
            continue
        if aula.presencas.exists():
            continue
        aula.status = Aula.STATUS_CANCELADA
        aula.save(update_fields=["status", "atualizado_em"])


@transaction.atomic
def sincronizar_aulas_da_turma(turma: Turma, horarios: list[dict]) -> None:
    _validar_horarios_obrigatorios(turma, horarios)
    pares_desejados = _normalizar_horarios(horarios) if turma.ativo else set()
    if turma.ativo:
        _criar_ou_atualizar_aulas(turma, horarios)
    _cancelar_aulas_futuras_removidas(turma, pares_desejados)


def fechar_chamada_aula(aula: Aula, usuario, agora=None) -> Aula:
    if aula.status == Aula.STATUS_CANCELADA:
        raise DomainValidationError("Nao e possivel fechar chamada de aula cancelada.")

    agora = agora or timezone.now()
    if aula.status != Aula.STATUS_FECHADA:
        aula.status = Aula.STATUS_FECHADA
    aula.fechada_em = agora
    aula.fechada_por = usuario
    aula.save(update_fields=["status", "fechada_em", "fechada_por", "atualizado_em"])
    return aula
