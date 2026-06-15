from datetime import datetime

from django.utils import timezone

from api.models import Aula, HorarioAula
from .errors import DomainValidationError


def calcular_intervalo_aula(horario: HorarioAula, data_aula):
    padrao = horario.horario_padrao
    inicio = timezone.make_aware(datetime.combine(data_aula, padrao.horario_inicio))
    fim = timezone.make_aware(datetime.combine(data_aula, padrao.horario_fim))
    return inicio, fim


def obter_ou_criar_aula(horario: HorarioAula, data_aula):
    if data_aula.weekday() != horario.horario_padrao.weekday_python:
        raise DomainValidationError("A data da aula nao corresponde ao dia da semana do horario.")

    periodo = horario.turma.periodo_letivo
    if data_aula < periodo.data_inicio or data_aula > periodo.data_fim:
        raise DomainValidationError("A data da aula deve estar dentro do periodo letivo da turma.")

    inicio, fim = calcular_intervalo_aula(horario, data_aula)
    aula, criada = Aula.objects.get_or_create(
        horario=horario,
        data=data_aula,
        defaults={
            "inicio": inicio,
            "fim": fim,
            "status": Aula.STATUS_PLANEJADA,
        },
    )
    return aula, criada


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


def listar_aulas_do_dia(data, sala=None):
    horarios = HorarioAula.objects.select_related(
        "turma",
        "turma__disciplina",
        "turma__periodo_letivo",
        "sala",
        "horario_padrao",
    ).filter(
        turma__periodo_letivo__data_inicio__lte=data,
        turma__periodo_letivo__data_fim__gte=data,
        turma__ativo=True,
        turma__disciplina__ativo=True,
        sala__ativo=True,
        horario_padrao__ativo=True,
        ativo=True,
        horario_padrao__dia_semana=data.weekday() + 2,
    )
    if sala is not None:
        horarios = horarios.filter(sala=sala)

    aulas = []
    for horario in horarios:
        aula, _ = obter_ou_criar_aula(horario, data)
        if aula.status != Aula.STATUS_CANCELADA:
            aulas.append(aula)
    return aulas
