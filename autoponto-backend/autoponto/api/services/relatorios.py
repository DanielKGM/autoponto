from django.utils import timezone

from api.models import Aula, MatriculaTurma, PapelUsuario, RegistroPresenca, Turma, Usuario


def usuario_pode_acessar_turma(usuario: Usuario, turma: Turma) -> bool:
    if usuario.papel == PapelUsuario.ADMINISTRADOR:
        return True
    if usuario.papel == PapelUsuario.PROFESSOR:
        return turma.professores.filter(id=usuario.id).exists()
    if usuario.papel == PapelUsuario.ALUNO:
        return MatriculaTurma.objects.filter(turma=turma, aluno=usuario, ativo=True).exists()
    return False


def aulas_da_turma(turma: Turma, inicio, fim):
    return list(
        Aula.objects.select_related("turma", "turma__disciplina", "sala", "horario_padrao")
        .filter(turma=turma, data__gte=inicio, data__lte=fim)
        .exclude(status=Aula.STATUS_CANCELADA)
        .order_by("data", "inicio")
    )


def payload_turma(turma: Turma) -> dict:
    return {
        "turma_id": str(turma.id),
        "codigo": turma.codigo,
        "nome": f"{turma.disciplina.nome} - {turma.codigo}",
        "disciplina_id": str(turma.disciplina_id),
        "disciplina": turma.disciplina.nome,
        "periodo_letivo_id": str(turma.periodo_letivo_id),
        "periodo_letivo": turma.periodo_letivo.nome,
        "curso": turma.disciplina.curso.nome,
        "professores": [
            {"id": str(professor.id), "nome": professor.nome_completo or professor.username}
            for professor in turma.professores.all()
        ],
    }


def turmas_do_aluno(aluno: Usuario):
    matriculas = (
        MatriculaTurma.objects.select_related(
            "turma",
            "turma__disciplina",
            "turma__disciplina__curso",
            "turma__periodo_letivo",
        )
        .prefetch_related("turma__professores")
        .filter(aluno=aluno, ativo=True, turma__periodo_letivo__ativo=True, turma__ativo=True)
    )
    return [payload_turma(matricula.turma) for matricula in matriculas]


def turmas_do_professor(professor: Usuario):
    turmas = (
        Turma.objects.select_related("disciplina", "disciplina__curso", "periodo_letivo")
        .prefetch_related("professores")
        .filter(professores=professor, ativo=True)
        .distinct()
    )
    return [payload_turma(turma) for turma in turmas]


def presencas_do_aluno(aluno: Usuario):
    registros = (
        RegistroPresenca.objects.select_related(
            "aula",
            "aula__turma",
            "aula__turma__disciplina",
            "aula__turma__periodo_letivo",
            "aula__sala",
        )
        .filter(aluno=aluno)
        .order_by("-aula__data", "aula__inicio")
    )
    return [payload_registro_presenca(registro) for registro in registros]


def payload_registro_presenca(registro: RegistroPresenca) -> dict:
    aula = registro.aula
    turma = aula.turma
    return {
        "presenca_id": str(registro.id),
        "aula_id": str(aula.id),
        "turma_id": str(turma.id),
        "disciplina": turma.disciplina.nome,
        "turma": turma.codigo,
        "periodo_letivo": turma.periodo_letivo.nome,
        "data": aula.data.isoformat(),
        "inicio": aula.inicio.isoformat(),
        "fim": aula.fim.isoformat(),
        "sala": aula.sala.nome,
        "status": registro.status,
        "registrado_em": registro.registrado_em.isoformat(),
        "origem": str(registro.registrado_por_dispositivo_id) if registro.registrado_por_dispositivo_id else None,
    }


def relatorio_presencas_turma_data(turma: Turma, data):
    aulas = aulas_da_turma(turma, data, data)
    aula_ids = [aula.id for aula in aulas]
    matriculas = MatriculaTurma.objects.select_related("aluno").filter(turma=turma, ativo=True).order_by(
        "aluno__nome_completo", "aluno__username"
    )
    registros = RegistroPresenca.objects.filter(aula_id__in=aula_ids).select_related("aluno")
    registros_por_aluno = {registro.aluno_id: registro for registro in registros}

    alunos = []
    for matricula in matriculas:
        registro = registros_por_aluno.get(matricula.aluno_id)
        alunos.append(
            {
                "aluno_id": str(matricula.aluno_id),
                "nome": matricula.aluno.nome_completo or matricula.aluno.username,
                "matricula": matricula.aluno.matricula,
                "status": registro.status if registro else RegistroPresenca.STATUS_AUSENTE,
                "registrado_em": registro.registrado_em.isoformat() if registro else None,
            }
        )

    presentes = sum(1 for aluno in alunos if aluno["status"] == RegistroPresenca.STATUS_PRESENTE)
    return {
        **payload_turma(turma),
        "data": data.isoformat(),
        "aulas": [
            {
                "aula_id": str(aula.id),
                "inicio": aula.inicio.isoformat(),
                "fim": aula.fim.isoformat(),
                "status": aula.status,
                "fechada_em": aula.fechada_em.isoformat() if aula.fechada_em else None,
                "fechada_por": str(aula.fechada_por_id) if aula.fechada_por_id else None,
                "sala": aula.sala.nome,
            }
            for aula in aulas
        ],
        "totais": {
            "presentes": presentes,
            "ausentes": len(alunos) - presentes,
            "matriculados": len(alunos),
        },
        "alunos": alunos,
    }


def relatorio_resumo_turma(turma: Turma, inicio=None, fim=None):
    inicio = inicio or turma.periodo_letivo.data_inicio
    fim = fim or min(turma.periodo_letivo.data_fim, timezone.localdate())
    aulas = aulas_da_turma(turma, inicio, fim)
    aula_ids = [aula.id for aula in aulas]
    total_aulas = len(aulas)
    matriculas = MatriculaTurma.objects.select_related("aluno").filter(turma=turma, ativo=True).order_by(
        "aluno__nome_completo", "aluno__username"
    )
    presencas = RegistroPresenca.objects.filter(aula_id__in=aula_ids, status=RegistroPresenca.STATUS_PRESENTE)
    presencas_por_aluno = {}
    for registro in presencas:
        presencas_por_aluno[registro.aluno_id] = presencas_por_aluno.get(registro.aluno_id, 0) + 1

    alunos = []
    for matricula in matriculas:
        total_presencas = presencas_por_aluno.get(matricula.aluno_id, 0)
        faltas = max(total_aulas - total_presencas, 0)
        percentual = round((total_presencas / total_aulas) * 100, 2) if total_aulas else 0.0
        alunos.append(
            {
                "aluno_id": str(matricula.aluno_id),
                "nome": matricula.aluno.nome_completo or matricula.aluno.username,
                "matricula": matricula.aluno.matricula,
                "presencas": total_presencas,
                "faltas": faltas,
                "percentual_presenca": percentual,
            }
        )

    return {
        **payload_turma(turma),
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "total_aulas": total_aulas,
        "alunos": alunos,
    }


def historico_presencas_aluno(aluno: Usuario, turma_id=None, periodo_letivo_id=None, turma_ids_permitidas=None):
    registros = RegistroPresenca.objects.select_related(
        "aula",
        "aula__turma",
        "aula__turma__disciplina",
        "aula__turma__periodo_letivo",
        "aula__sala",
    ).filter(aluno=aluno)
    if turma_id:
        registros = registros.filter(aula__turma_id=turma_id)
    elif turma_ids_permitidas is not None:
        registros = registros.filter(aula__turma_id__in=turma_ids_permitidas)
    if periodo_letivo_id:
        registros = registros.filter(aula__turma__periodo_letivo_id=periodo_letivo_id)

    return {
        "aluno_id": str(aluno.id),
        "nome": aluno.nome_completo or aluno.username,
        "matricula": aluno.matricula,
        "presencas": [payload_registro_presenca(registro) for registro in registros.order_by("-aula__data")],
    }
