from django.utils import timezone

from api.models import (
    Aula,
    DispositivoEsp32,
    EmbeddingFacial,
    EventoReconhecimento,
    MatriculaTurma,
    PapelUsuario,
    PeriodoLetivo,
    RegistroPresenca,
    Turma,
    Usuario,
)
from api.selectors.aulas import com_status_aula, status_aula


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
        com_status_aula(
            Aula.objects.select_related("turma", "turma__disciplina", "sala", "horario_padrao")
        )
        .filter(turma=turma, data__gte=inicio, data__lte=fim)
        .filter(cancelada_em__isnull=True)
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


def calendario_aulas_usuario(usuario: Usuario, inicio, fim) -> dict:
    if usuario.papel == PapelUsuario.ALUNO:
        return calendario_aulas_aluno(usuario, inicio, fim)
    return calendario_aulas_professor(usuario, inicio, fim)


def calendario_aulas_aluno(aluno: Usuario, inicio, fim) -> dict:
    aulas = list(
        com_status_aula(
            Aula.objects.select_related(
                "turma",
                "turma__disciplina",
                "turma__periodo_letivo",
                "sala",
            )
        )
        .filter(
            turma__matriculas__aluno=aluno,
            turma__matriculas__ativo=True,
            turma__ativo=True,
            data__gte=inicio,
            data__lte=fim,
        )
        .distinct()
        .order_by("data", "inicio")
    )
    aula_ids = [aula.id for aula in aulas]
    registros = RegistroPresenca.objects.filter(aluno=aluno, aula_id__in=aula_ids)
    registros_por_aula = {registro.aula_id: registro for registro in registros}

    return {
        "visualizacao": "ALUNO",
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "aulas": [
            payload_aula_calendario_aluno(aula, registros_por_aula.get(aula.id))
            for aula in aulas
        ],
    }


def calendario_aulas_professor(usuario: Usuario, inicio, fim) -> dict:
    aulas = com_status_aula(
        Aula.objects.select_related(
            "turma",
            "turma__disciplina",
            "turma__periodo_letivo",
            "sala",
        )
    ).filter(
            turma__ativo=True,
            data__gte=inicio,
            data__lte=fim,
    )
    if usuario.papel == PapelUsuario.PROFESSOR:
        aulas = aulas.filter(turma__professores=usuario)
    aulas = aulas.distinct().order_by("data", "inicio")

    return {
        "visualizacao": "PROFESSOR",
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "aulas": [payload_aula_calendario_professor(aula) for aula in aulas],
    }


def status_aluno_calendario(aula: Aula, registro: RegistroPresenca | None) -> str:
    estado = status_aula(aula)
    if estado == Aula.STATUS_CANCELADA:
        return "NAO_APLICAVEL"
    if registro:
        return registro.status
    if estado == Aula.STATUS_FECHADA:
        return RegistroPresenca.STATUS_AUSENTE
    return "PENDENTE"


def payload_aula_calendario_aluno(aula: Aula, registro: RegistroPresenca | None) -> dict:
    turma = aula.turma
    return {
        "aula_id": str(aula.id),
        "turma_id": str(turma.id),
        "disciplina": turma.disciplina.nome,
        "turma": turma.codigo,
        "periodo_letivo": turma.periodo_letivo.nome,
        "data": aula.data.isoformat(),
        "inicio": aula.inicio.isoformat(),
        "fim": aula.fim.isoformat(),
        "sala": aula.sala.nome,
        "status_aula": status_aula(aula),
        "status_aluno": status_aluno_calendario(aula, registro),
        "presenca_id": str(registro.id) if registro else None,
        "registrado_em": registro.registrado_em.isoformat() if registro else None,
    }


def payload_aula_calendario_professor(aula: Aula) -> dict:
    turma = aula.turma
    return {
        "aula_id": str(aula.id),
        "turma_id": str(turma.id),
        "disciplina": turma.disciplina.nome,
        "turma": turma.codigo,
        "periodo_letivo": turma.periodo_letivo.nome,
        "data": aula.data.isoformat(),
        "inicio": aula.inicio.isoformat(),
        "fim": aula.fim.isoformat(),
        "sala": aula.sala.nome,
        "status_aula": status_aula(aula),
        "status_aluno": None,
        "presenca_id": None,
        "registrado_em": None,
    }


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
                "status": status_aula(aula),
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
    aulas = _aulas_fechadas_da_turma(turma, inicio, fim)
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


def _nome_usuario(usuario: Usuario) -> str:
    return usuario.nome_completo or usuario.username


def _percentual(parte: int, total: int) -> float:
    return round((parte / total) * 100, 2) if total else 0.0


def _turmas_ativas_do_aluno(aluno: Usuario):
    return (
        Turma.objects.select_related("disciplina", "disciplina__curso", "periodo_letivo")
        .prefetch_related("professores")
        .filter(matriculas__aluno=aluno, matriculas__ativo=True, ativo=True)
        .distinct()
    )


def _turmas_ativas_do_professor(usuario: Usuario):
    queryset = (
        Turma.objects.select_related("disciplina", "disciplina__curso", "periodo_letivo")
        .prefetch_related("professores")
        .filter(ativo=True)
        .distinct()
    )
    if usuario.papel == PapelUsuario.PROFESSOR:
        queryset = queryset.filter(professores=usuario)
    return queryset


def _periodos_do_aluno(aluno: Usuario):
    return (
        PeriodoLetivo.objects.filter(turmas__matriculas__aluno=aluno, turmas__matriculas__ativo=True)
        .distinct()
        .order_by("-data_inicio", "nome")
    )


def _payload_periodo(periodo: PeriodoLetivo) -> dict:
    return {
        "id": str(periodo.id),
        "nome": periodo.nome,
        "data_inicio": periodo.data_inicio.isoformat(),
        "data_fim": periodo.data_fim.isoformat(),
        "ativo": periodo.ativo,
    }


def _periodo_frequencia_aluno(aluno: Usuario, periodo_letivo_id=None):
    periodos = list(_periodos_do_aluno(aluno))
    if periodo_letivo_id:
        return next((periodo for periodo in periodos if str(periodo.id) == str(periodo_letivo_id)), None), periodos
    ativo = next((periodo for periodo in periodos if periodo.ativo), None)
    return ativo or (periodos[0] if periodos else None), periodos


def _aulas_fechadas_da_turma(turma: Turma, inicio=None, fim=None):
    queryset = com_status_aula(
        Aula.objects.select_related("turma", "turma__disciplina", "sala", "horario_padrao").filter(turma=turma)
    )
    if inicio:
        queryset = queryset.filter(data__gte=inicio)
    if fim:
        queryset = queryset.filter(data__lte=fim)
    return list(queryset.filter(status=Aula.STATUS_FECHADA).order_by("data", "inicio"))


def _resumo_frequencia_turma_para_aluno(turma: Turma, aluno: Usuario) -> dict:
    aulas = _aulas_fechadas_da_turma(turma, turma.periodo_letivo.data_inicio, turma.periodo_letivo.data_fim)
    total = len(aulas)
    presencas = RegistroPresenca.objects.filter(
        aluno=aluno,
        aula_id__in=[aula.id for aula in aulas],
        status=RegistroPresenca.STATUS_PRESENTE,
    ).count()
    faltas = max(total - presencas, 0)
    return {
        **payload_turma(turma),
        **payload_ultimo_sync_turma(turma),
        "total_aulas_fechadas": total,
        "presencas": presencas,
        "faltas": faltas,
        "percentual": _percentual(presencas, total),
    }


def resumo_frequencia_aluno(aluno: Usuario, periodo_letivo_id=None) -> dict:
    periodo, periodos = _periodo_frequencia_aluno(aluno, periodo_letivo_id)
    turmas = _turmas_ativas_do_aluno(aluno)
    if periodo:
        turmas = turmas.filter(periodo_letivo=periodo)
    turmas_payload = [_resumo_frequencia_turma_para_aluno(turma, aluno) for turma in turmas]
    total = sum(item["total_aulas_fechadas"] for item in turmas_payload)
    presencas = sum(item["presencas"] for item in turmas_payload)
    faltas = sum(item["faltas"] for item in turmas_payload)
    return {
        "aluno_id": str(aluno.id),
        "periodo_letivo_id": str(periodo.id) if periodo else None,
        "periodo_letivo": periodo.nome if periodo else None,
        "periodos": [_payload_periodo(item) for item in periodos],
        "resumo": {
            "total_aulas_fechadas": total,
            "presencas": presencas,
            "faltas": faltas,
            "percentual": _percentual(presencas, total),
        },
        "turmas": turmas_payload,
    }


def _status_aluno_resumo(aula: Aula, registro: RegistroPresenca | None) -> str:
    if registro:
        return RegistroPresenca.STATUS_PRESENTE
    estado = status_aula(aula)
    if estado == Aula.STATUS_CANCELADA:
        return "NAO_APLICAVEL"
    if estado == Aula.STATUS_FECHADA:
        return RegistroPresenca.STATUS_AUSENTE
    return "PENDENTE"


def _payload_aula_resumo(aula: Aula, status_aluno=None) -> dict:
    payload = payload_aula_calendario_professor(aula)
    payload["status_aluno"] = status_aluno
    return payload


def dashboard_aluno(aluno: Usuario) -> dict:
    hoje = timezone.localdate()
    turmas = _turmas_ativas_do_aluno(aluno)
    aulas_base = com_status_aula(
        Aula.objects.select_related("turma", "turma__disciplina", "turma__periodo_letivo", "sala")
        .filter(turma__in=turmas)
        .distinct()
    )
    aulas_hoje = list(aulas_base.filter(data=hoje).order_by("inicio"))
    proximas = list(
        aulas_base.filter(data__gt=hoje)
        .exclude(status__in=[Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA])
        .order_by("data", "inicio")[:6]
    )
    ultimas_aulas = list(aulas_base.filter(data__lte=hoje).order_by("-data", "-inicio")[:8])
    aula_ids = [aula.id for aula in [*aulas_hoje, *proximas, *ultimas_aulas]]
    registros = RegistroPresenca.objects.filter(aluno=aluno, aula_id__in=aula_ids)
    registros_por_aula = {registro.aula_id: registro for registro in registros}
    frequencia = resumo_frequencia_aluno(aluno)
    pendentes = aulas_base.exclude(status__in=[Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA]).count()
    return {
        "gerado_em": timezone.now().isoformat(),
        "biometria_cadastrada": EmbeddingFacial.objects.filter(
            aluno=aluno,
            ativo=True,
            status=EmbeddingFacial.STATUS_ATIVO,
        ).exists(),
        "aulas_hoje": [
            _payload_aula_resumo(aula, _status_aluno_resumo(aula, registros_por_aula.get(aula.id)))
            for aula in aulas_hoje
        ],
        "proximas_aulas": [
            _payload_aula_resumo(aula, _status_aluno_resumo(aula, registros_por_aula.get(aula.id)))
            for aula in proximas
        ],
        "resumo": {
            "total_fechadas": frequencia["resumo"]["total_aulas_fechadas"],
            "presentes": frequencia["resumo"]["presencas"],
            "ausentes": frequencia["resumo"]["faltas"],
            "pendentes": pendentes,
            "percentual": frequencia["resumo"]["percentual"],
        },
        "frequencia_por_turma": frequencia["turmas"],
        "ultimas_presencas": [
            {
                **_payload_aula_resumo(aula, _status_aluno_resumo(aula, registros_por_aula.get(aula.id))),
                "status": _status_aluno_resumo(aula, registros_por_aula.get(aula.id)),
            }
            for aula in ultimas_aulas
        ],
    }


def dashboard_professor(usuario: Usuario) -> dict:
    hoje = timezone.localdate()
    turmas = _turmas_ativas_do_professor(usuario)
    aulas = com_status_aula(
        Aula.objects.select_related("turma", "turma__disciplina", "turma__periodo_letivo", "sala")
        .filter(turma__in=turmas)
        .distinct()
    )
    aulas_hoje = list(aulas.filter(data=hoje).order_by("inicio"))
    abertas = list(aulas.filter(status=Aula.STATUS_ABERTA).order_by("data", "inicio"))
    pendentes = list(aulas.filter(status=Aula.STATUS_PLANEJADA, data__lte=hoje).order_by("data", "inicio"))
    presencas = (
        RegistroPresenca.objects.select_related("aluno", "aula", "aula__turma", "aula__turma__disciplina", "aula__sala")
        .filter(aula__turma__in=turmas)
        .order_by("-registrado_em")[:8]
    )
    return {
        "gerado_em": timezone.now().isoformat(),
        "aulas_hoje": [_payload_aula_resumo(aula) for aula in aulas_hoje],
        "chamadas_abertas": [_payload_aula_resumo(aula) for aula in abertas[:8]],
        "chamadas_pendentes": [_payload_aula_resumo(aula) for aula in pendentes[:8]],
        "turmas": [payload_turma(turma) for turma in turmas],
        "presencas_recentes": [
            {
                **payload_registro_presenca(registro),
                "aluno_id": str(registro.aluno_id),
                "aluno": _nome_usuario(registro.aluno),
            }
            for registro in presencas
        ],
        "totais": {
            "aulas_hoje": len(aulas_hoje),
            "chamadas_abertas": len(abertas),
            "chamadas_pendentes": len(pendentes),
            "turmas_ministradas": turmas.count(),
        },
    }


def resumo_frequencia_turma(turma: Turma) -> dict:
    aulas = _aulas_fechadas_da_turma(turma, turma.periodo_letivo.data_inicio, turma.periodo_letivo.data_fim)
    aula_ids = [aula.id for aula in aulas]
    total = len(aulas)
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
        faltas = max(total - total_presencas, 0)
        alunos.append(
            {
                "aluno_id": str(matricula.aluno_id),
                "nome": _nome_usuario(matricula.aluno),
                "matricula": matricula.aluno.matricula,
                "total_aulas_fechadas": total,
                "presencas": total_presencas,
                "faltas": faltas,
                "percentual": _percentual(total_presencas, total),
            }
        )
    return {
        **payload_turma(turma),
        "resumo": {
            "total_aulas_fechadas": total,
            "presencas": sum(item["presencas"] for item in alunos),
            "faltas": sum(item["faltas"] for item in alunos),
            "percentual": _percentual(sum(item["presencas"] for item in alunos), total * len(alunos)),
        },
        "alunos": alunos,
    }


def payload_ultimo_sync_turma(turma: Turma) -> dict:
    dispositivo_com_sync = (
        DispositivoEsp32.objects.select_related("no")
        .filter(
            ativo=True,
            no__isnull=False,
            no__ultimo_sync_em__isnull=False,
            sala__aulas__turma=turma,
        )
        .order_by("-no__ultimo_sync_em", "codigo")
        .first()
    )
    dispositivo = dispositivo_com_sync or (
        DispositivoEsp32.objects.select_related("no")
        .filter(ativo=True, no__isnull=False, sala__aulas__turma=turma)
        .order_by("codigo")
        .first()
    )
    no = dispositivo.no if dispositivo else None
    return {
        "ultimo_sync_no_borda": no.ultimo_sync_em.isoformat() if no and no.ultimo_sync_em else None,
        "no_borda_codigo": no.codigo if no else None,
        "no_borda_nome": no.nome if no else None,
    }


def biometrias_do_aluno(aluno: Usuario) -> list[dict]:
    embeddings = EmbeddingFacial.objects.filter(aluno=aluno).order_by("-criado_em")
    return [
        {
            "id": str(embedding.id),
            "versao_modelo": embedding.versao_modelo,
            "status": embedding.status,
            "ativo": embedding.ativo,
            "possui_vetor": bool(embedding.vetor),
            "criado_em": embedding.criado_em.isoformat(),
            "atualizado_em": embedding.atualizado_em.isoformat(),
            "revogado_em": embedding.revogado_em.isoformat() if embedding.revogado_em else None,
        }
        for embedding in embeddings
    ]


def eventos_reconhecimento_do_aluno(aluno: Usuario, limite: int = 20) -> list[dict]:
    eventos = (
        EventoReconhecimento.objects.select_related(
            "dispositivo",
            "aula",
            "aula__turma",
            "aula__turma__disciplina",
            "aula__sala",
            "embedding",
        )
        .filter(aluno_candidato=aluno)
        .order_by("-ocorrido_em")[:limite]
    )
    payload = []
    for evento in eventos:
        aula = evento.aula
        turma = aula.turma if aula else None
        embedding = evento.embedding
        payload.append(
            {
                "id": str(evento.id),
                "aula_id": str(aula.id) if aula else None,
                "turma_id": str(turma.id) if turma else None,
                "disciplina": turma.disciplina.nome if turma else None,
                "turma": turma.codigo if turma else None,
                "data": aula.data.isoformat() if aula else None,
                "inicio": aula.inicio.isoformat() if aula else None,
                "fim": aula.fim.isoformat() if aula else None,
                "sala": aula.sala.nome if aula else None,
                "dispositivo": evento.dispositivo.codigo,
                "confianca": float(evento.confianca),
                "reconhecido": evento.reconhecido,
                "ocorrido_em": evento.ocorrido_em.isoformat(),
                "embedding_id": str(embedding.id) if embedding else None,
                "embedding_status": embedding.status if embedding else None,
                "embedding_criado_em": embedding.criado_em.isoformat() if embedding else None,
            }
        )
    return payload


def _payload_turma_detalhe(turma: Turma) -> dict:
    return {
        **payload_turma(turma),
        "total_alunos": MatriculaTurma.objects.filter(turma=turma, ativo=True).count(),
    }


def _payload_aula_detalhe(aula: Aula, usuario: Usuario) -> dict:
    payload = _payload_aula_resumo(aula)
    agora = timezone.now()
    estado = status_aula(aula, agora=agora)
    pode_gerenciar = usuario.papel in {PapelUsuario.PROFESSOR, PapelUsuario.ADMINISTRADOR}
    payload["pode_abrir_chamada"] = False
    payload["pode_fechar_chamada"] = (
        pode_gerenciar
        and estado == Aula.STATUS_ABERTA
        and agora >= aula.inicio
    )
    payload["fechada_em"] = aula.fechada_em.isoformat() if aula.fechada_em else None
    payload["fechada_por"] = str(aula.fechada_por_id) if aula.fechada_por_id else None
    return payload


def detalhe_turma_aula(usuario: Usuario, turma: Turma, aula: Aula | None = None) -> dict:
    proximas_aulas = (
        com_status_aula(Aula.objects.select_related("turma", "turma__disciplina", "turma__periodo_letivo", "sala"))
        .filter(turma=turma, data__gte=timezone.localdate())
        .order_by("data", "inicio")[:6]
    )
    payload = {
        "turma": _payload_turma_detalhe(turma),
        "aula": _payload_aula_detalhe(aula, usuario) if aula else None,
        "proximas_aulas": [_payload_aula_resumo(item) for item in proximas_aulas],
        "alunos": [],
        "eventos_reconhecimento": [],
        "resumo": None,
        "instrucao": "Acesse o calendario e selecione uma aula para visualizar a chamada.",
    }
    if not aula:
        return payload

    matriculas = MatriculaTurma.objects.select_related("aluno").filter(turma=turma, ativo=True).order_by(
        "aluno__nome_completo", "aluno__username"
    )
    registros = RegistroPresenca.objects.filter(aula=aula)
    registros_por_aluno = {registro.aluno_id: registro for registro in registros}
    alunos = []
    for matricula in matriculas:
        registro = registros_por_aluno.get(matricula.aluno_id)
        status = _status_aluno_resumo(aula, registro)
        alunos.append(
            {
                "aluno_id": str(matricula.aluno_id),
                "nome": _nome_usuario(matricula.aluno),
                "matricula": matricula.aluno.matricula,
                "status": status,
                "registrado_em": registro.registrado_em.isoformat() if registro else None,
                "presenca_id": str(registro.id) if registro else None,
            }
        )
    payload["alunos"] = alunos
    payload["resumo"] = {
        "presentes": sum(1 for item in alunos if item["status"] == RegistroPresenca.STATUS_PRESENTE),
        "ausentes": sum(1 for item in alunos if item["status"] == RegistroPresenca.STATUS_AUSENTE),
        "pendentes": sum(1 for item in alunos if item["status"] == "PENDENTE"),
        "matriculados": len(alunos),
    }
    if usuario.papel in {PapelUsuario.PROFESSOR, PapelUsuario.ADMINISTRADOR}:
        eventos = (
            EventoReconhecimento.objects.select_related("dispositivo", "aluno_candidato", "embedding")
            .filter(aula=aula)
            .order_by("-ocorrido_em")
        )
        payload["eventos_reconhecimento"] = [
            {
                "id": str(evento.id),
                "dispositivo": evento.dispositivo.codigo,
                "aluno_id": str(evento.aluno_candidato_id) if evento.aluno_candidato_id else None,
                "aluno": _nome_usuario(evento.aluno_candidato) if evento.aluno_candidato else None,
                "confianca": float(evento.confianca),
                "reconhecido": evento.reconhecido,
                "ocorrido_em": evento.ocorrido_em.isoformat(),
                "embedding_id": str(evento.embedding_id) if evento.embedding_id else None,
                "embedding_status": evento.embedding.status if evento.embedding else None,
            }
            for evento in eventos
        ]
    return payload
