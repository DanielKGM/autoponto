from datetime import datetime

from django.utils import timezone

from api.models import Aula, HorarioAula
from .errors import DomainValidationError


def obter_ou_criar_aula(horario: HorarioAula, data_aula):
    if data_aula.weekday() != horario.dia_semana:
        raise DomainValidationError("A data da aula não corresponde ao dia da semana do horário.")

    inicio = timezone.make_aware(datetime.combine(data_aula, horario.horario_inicio))
    fim = timezone.make_aware(datetime.combine(data_aula, horario.horario_fim))
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
