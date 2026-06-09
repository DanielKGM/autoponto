from datetime import datetime, timedelta

from django.utils import timezone

from api.models import Aula, HorarioAula
from .errors import DomainValidationError


def calcular_intervalo_aula(horario: HorarioAula, data_aula):
    inicio = timezone.make_aware(datetime.combine(data_aula, horario.horario_inicio))
    fim = timezone.make_aware(datetime.combine(data_aula, horario.horario_fim))
    return inicio, fim


def calcular_janela_chamada(horario: HorarioAula, data_aula):
    inicio, fim = calcular_intervalo_aula(horario, data_aula)
    chamada_inicio = inicio + timedelta(minutes=horario.abre_chamada_minutos)
    if horario.fecha_chamada_minutos is None:
        chamada_fim = fim
    else:
        chamada_fim = inicio + timedelta(minutes=horario.fecha_chamada_minutos)
    return chamada_inicio, chamada_fim


def obter_ou_criar_aula(horario: HorarioAula, data_aula):
    if data_aula.weekday() != horario.dia_semana:
        raise DomainValidationError("A data da aula não corresponde ao dia da semana do horário.")

    inicio, fim = calcular_intervalo_aula(horario, data_aula)
    chamada_inicio, chamada_fim = calcular_janela_chamada(horario, data_aula)
    aula, criada = Aula.objects.get_or_create(
        horario=horario,
        data=data_aula,
        defaults={
            "inicio": inicio,
            "fim": fim,
            "chamada_inicio": chamada_inicio,
            "chamada_fim": chamada_fim,
            "status": Aula.STATUS_PLANEJADA,
        },
    )
    return aula, criada


def recalcular_janelas_aulas_futuras(horario: HorarioAula, data_referencia=None) -> int:
    data_referencia = data_referencia or timezone.localdate()
    aulas = horario.aulas.filter(data__gte=data_referencia).exclude(
        status__in=[Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA]
    )

    atualizadas = 0
    for aula in aulas:
        chamada_inicio, chamada_fim = calcular_janela_chamada(horario, aula.data)
        if aula.chamada_inicio == chamada_inicio and aula.chamada_fim == chamada_fim:
            continue
        aula.chamada_inicio = chamada_inicio
        aula.chamada_fim = chamada_fim
        aula.save(update_fields=["chamada_inicio", "chamada_fim", "atualizado_em"])
        atualizadas += 1
    return atualizadas


def fechar_chamada_aula(aula: Aula, usuario, agora=None) -> Aula:
    if aula.status == Aula.STATUS_CANCELADA:
        raise DomainValidationError("Não é possível fechar chamada de aula cancelada.")

    agora = agora or timezone.now()
    if aula.status != Aula.STATUS_FECHADA:
        aula.status = Aula.STATUS_FECHADA
    aula.fechada_em = agora
    aula.fechada_por = usuario
    if aula.chamada_inicio < agora < aula.chamada_fim:
        aula.chamada_fim = agora
    aula.save(update_fields=["status", "fechada_em", "fechada_por", "chamada_fim", "atualizado_em"])
    return aula


def listar_aulas_do_dia(data, sala=None):
    horarios = HorarioAula.objects.select_related(
        "turma",
        "turma__disciplina",
        "turma__periodo_letivo",
        "sala",
    ).filter(
        turma__periodo_letivo__data_inicio__lte=data,
        turma__periodo_letivo__data_fim__gte=data,
        turma__ativo=True,
        turma__disciplina__ativo=True,
        sala__ativo=True,
        ativo=True,
        dia_semana=data.weekday(),
    )
    if sala is not None:
        horarios = horarios.filter(sala=sala)

    aulas = []
    for horario in horarios:
        aula, _ = obter_ou_criar_aula(horario, data)
        if aula.status != Aula.STATUS_CANCELADA:
            aulas.append(aula)
    return aulas
