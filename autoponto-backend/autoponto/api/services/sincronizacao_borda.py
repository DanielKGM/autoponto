from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from api.models import (
    Aula,
    ComandoBorda,
    DispositivoEsp32,
    EmbeddingFacial,
    EventoReconhecimento,
    MatriculaTurma,
    NoBorda,
    PapelUsuario,
    RegistroPresenca,
    Sala,
    Usuario,
)
from api.services.aulas import listar_aulas_do_dia


ENTIDADES_SYNC = ("locales", "devices", "lessons", "students", "enrollments", "face_embeddings")


def parsear_cursor(valor: str | None):
    if not valor:
        return None
    try:
        parseado = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parseado.tzinfo is None:
        return timezone.make_aware(parseado)
    return parseado


def decodificar_cursors(valor_bruto: str | None) -> dict[str, str]:
    if not valor_bruto:
        return {}
    try:
        import msgpack

        return msgpack.unpackb(bytes.fromhex(valor_bruto), raw=False)
    except Exception:
        return {}


def _intervalo_datas(data_inicio, data_fim):
    atual = data_inicio
    while atual <= data_fim:
        yield atual
        atual += timedelta(days=1)


def _iso(valor):
    return valor.isoformat().replace("+00:00", "Z")


def _max_cursor(itens) -> str:
    datas = [item.atualizado_em for item in itens if getattr(item, "atualizado_em", None)]
    return _iso(max(datas) if datas else timezone.now())


def _janela_padrao():
    hoje = timezone.localdate()
    return (
        hoje - timedelta(days=settings.EDGE_SYNC_DAYS_BACK),
        hoje + timedelta(days=settings.EDGE_SYNC_DAYS_FORWARD),
    )


def _resolver_janela(params):
    data_inicio, data_fim = _janela_padrao()
    if params.get("from_date"):
        data_inicio = datetime.fromisoformat(params["from_date"]).date()
    if params.get("to_date"):
        data_fim = datetime.fromisoformat(params["to_date"]).date()
    return data_inicio, data_fim


def _validar_no(no: NoBorda, identificador: str | None):
    if identificador and identificador not in {str(no.id), no.codigo}:
        raise ValidationError({"node_id": "Token do nó não corresponde ao node_id solicitado."})


def _dispositivos_do_no(no: NoBorda):
    return list(DispositivoEsp32.objects.select_related("sala").filter(no=no))


def _filtrar_alterados(queryset, cursor):
    cursor_parseado = parsear_cursor(cursor)
    if cursor_parseado is None:
        return queryset
    return queryset.filter(atualizado_em__gt=cursor_parseado)


def montar_payload_pull(no: NoBorda, query_params) -> dict:
    _validar_no(no, query_params.get("node_id"))

    cursors = decodificar_cursors(query_params.get("cursors"))
    data_inicio, data_fim = _resolver_janela(query_params)
    dispositivos = _dispositivos_do_no(no)
    dispositivos_ativos = [dispositivo for dispositivo in dispositivos if dispositivo.ativo and dispositivo.sala_id]
    salas_do_no = [dispositivo.sala for dispositivo in dispositivos if dispositivo.sala_id]
    salas_ativas = [sala for sala in salas_do_no if isinstance(sala, Sala) and sala.ativo]

    aulas = []
    for data in _intervalo_datas(data_inicio, data_fim):
        for sala in salas_ativas:
            aulas.extend(listar_aulas_do_dia(data, sala=sala))
    aulas_disponiveis = [
        aula for aula in aulas if aula.status not in {Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA}
    ]

    turmas = {aula.horario.turma_id for aula in aulas_disponiveis}
    matriculas = list(
        MatriculaTurma.objects.select_related("aluno").filter(
            turma_id__in=turmas,
            ativo=True,
            aluno__papel=PapelUsuario.ALUNO,
            aluno__is_active=True,
        )
    )
    aluno_ids = {matricula.aluno_id for matricula in matriculas}
    alunos = list(Usuario.objects.filter(id__in=aluno_ids).order_by("username"))
    embeddings = list(
        EmbeddingFacial.objects.select_related("perfil", "perfil__aluno").filter(
            perfil__aluno_id__in=aluno_ids,
            ativo=True,
            status="ATIVO",
        )
    )

    aulas_por_turma = {}
    for aula in aulas_disponiveis:
        aulas_por_turma.setdefault(aula.horario.turma_id, []).append(aula)

    dados = {
        "locales": [
            {"id": str(sala.id), "name": sala.nome}
            for sala in sorted(set(salas_ativas), key=lambda item: item.nome)
        ],
        "devices": [
            {"id": str(dispositivo.id), "locale_id": str(dispositivo.sala_id), "active": dispositivo.ativo}
            for dispositivo in dispositivos_ativos
        ],
        "lessons": [
            {
                "id": str(aula.id),
                "name": f"{aula.horario.turma.disciplina.nome} - {aula.horario.turma.codigo}",
                "locale_id": str(aula.horario.sala_id),
                "starts_at": _iso(aula.inicio),
                "ends_at": _iso(aula.fim),
                "attendance_starts_at": _iso(aula.chamada_inicio),
                "attendance_ends_at": _iso(aula.chamada_fim),
                "status": aula.status,
            }
            for aula in aulas_disponiveis
        ],
        "students": [
            {
                "id": str(aluno.id),
                "registration": aluno.matricula,
                "name": aluno.nome_completo or aluno.username,
                "active": aluno.is_active,
            }
            for aluno in alunos
        ],
        "enrollments": [
            {"lesson_id": str(aula.id), "student_id": str(matricula.aluno_id)}
            for matricula in matriculas
            for aula in aulas_por_turma.get(matricula.turma_id, [])
        ],
        "face_embeddings": [
            {"id": str(embedding.id), "student_id": str(embedding.perfil.aluno_id), "embedding": embedding.vetor}
            for embedding in embeddings
        ],
    }

    dispositivos_inativos = _filtrar_alterados(
        DispositivoEsp32.objects.filter(no=no, ativo=False),
        cursors.get("devices"),
    )
    salas_inativas = _filtrar_alterados(
        Sala.objects.filter(id__in=[sala.id for sala in salas_do_no if sala], ativo=False),
        cursors.get("locales"),
    )
    aulas_canceladas = _filtrar_alterados(
        Aula.objects.filter(
            horario__sala_id__in=[sala.id for sala in salas_do_no if sala],
            data__gte=data_inicio,
            data__lte=data_fim,
        ).filter(
            Q(status__in=[Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA])
            | Q(horario__ativo=False)
            | Q(horario__turma__ativo=False)
        ),
        cursors.get("lessons"),
    )
    matriculas_inativas = _filtrar_alterados(
        MatriculaTurma.objects.filter(turma_id__in=turmas, ativo=False),
        cursors.get("enrollments"),
    )
    alunos_inativos = _filtrar_alterados(
        Usuario.objects.filter(id__in=aluno_ids, is_active=False),
        cursors.get("students"),
    )
    embeddings_inativos = _filtrar_alterados(
        EmbeddingFacial.objects.filter(perfil__aluno_id__in=aluno_ids).filter(Q(ativo=False) | ~Q(status="ATIVO")),
        cursors.get("face_embeddings"),
    )

    deletados = {
        "locales": [str(sala.id) for sala in salas_inativas],
        "devices": [str(dispositivo.id) for dispositivo in dispositivos_inativos],
        "lessons": [str(aula.id) for aula in aulas_canceladas],
        "students": [str(aluno.id) for aluno in alunos_inativos],
        "enrollments": [
            {"lesson_id": str(aula.id), "student_id": str(matricula.aluno_id)}
            for matricula in matriculas_inativas
            for aula in aulas_por_turma.get(matricula.turma_id, [])
        ],
        "face_embeddings": [str(embedding.id) for embedding in embeddings_inativos],
    }

    return {
        "data": dados,
        "deleted": deletados,
        "cursors": {
            "locales": _max_cursor(salas_do_no),
            "devices": _max_cursor(dispositivos),
            "lessons": _max_cursor(aulas),
            "students": _max_cursor(alunos),
            "enrollments": _max_cursor(matriculas),
            "face_embeddings": _max_cursor(embeddings),
        },
    }


def receber_presencas_borda(no: NoBorda, payload: dict) -> dict:
    _validar_no(no, payload.get("node_id"))

    ids_sincronizados = []
    for evento in payload.get("events", []):
        id_evento = evento.get("id")
        if not id_evento:
            raise ValidationError({"events": "Todo evento deve incluir um id."})
        ids_sincronizados.append(_receber_evento_borda(no, evento))
    return {"synced_ids": ids_sincronizados}


@transaction.atomic
def _receber_evento_borda(no: NoBorda, evento: dict) -> str:
    id_evento = evento["id"]
    existente = EventoReconhecimento.objects.filter(id_evento_origem=id_evento).first()
    if existente:
        return id_evento

    try:
        dispositivo = DispositivoEsp32.objects.get(id=evento["device_id"], no=no, ativo=True)
        aula = Aula.objects.select_related("horario", "horario__turma").get(id=evento["lesson_id"])
        aluno = Usuario.objects.get(id=evento["student_id"], papel=PapelUsuario.ALUNO, is_active=True)
    except (DispositivoEsp32.DoesNotExist, Aula.DoesNotExist, Usuario.DoesNotExist) as exc:
        raise ValidationError({"events": "Evento referencia nó, dispositivo, aula ou aluno desconhecido."}) from exc

    if aula.horario.sala_id != dispositivo.sala_id:
        raise ValidationError({"events": "A aula do evento não pertence à sala do dispositivo."})

    matriculado = MatriculaTurma.objects.filter(turma=aula.horario.turma, aluno=aluno, ativo=True).exists()
    if not matriculado:
        raise ValidationError({"events": "Aluno não está matriculado na aula enviada."})

    reconhecido_em = datetime.fromisoformat(str(evento["recognized_at"]).replace("Z", "+00:00"))
    if reconhecido_em.tzinfo is None:
        reconhecido_em = timezone.make_aware(reconhecido_em)

    if aula.status in {Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA}:
        raise ValidationError({"events": "A chamada da aula está fechada ou cancelada."})
    if reconhecido_em < aula.chamada_inicio or reconhecido_em > aula.chamada_fim:
        raise ValidationError({"events": "Evento fora da janela de chamada da aula."})

    try:
        RegistroPresenca.objects.update_or_create(
            aula=aula,
            aluno=aluno,
            defaults={
                "status": RegistroPresenca.STATUS_PRESENTE,
                "registrado_em": reconhecido_em,
                "registrado_por_dispositivo": dispositivo,
            },
        )
    except DjangoValidationError as exc:
        raise ValidationError(exc.message_dict) from exc

    EventoReconhecimento.objects.create(
        id_evento_origem=id_evento,
        dispositivo=dispositivo,
        aula=aula,
        aluno_candidato=aluno,
        confianca=Decimal(str(evento.get("score", 0))).quantize(Decimal("0.0001")),
        reconhecido=True,
        ocorrido_em=reconhecido_em,
    )
    if aula.status == Aula.STATUS_PLANEJADA:
        aula.status = Aula.STATUS_ABERTA
        aula.save(update_fields=["status", "atualizado_em"])
    return id_evento


def criar_comando_por_interscity(payload_comando: dict) -> ComandoBorda:
    uuid = payload_comando.get("uuid")
    capacidade = payload_comando.get("capability", "")
    id_origem = payload_comando.get("_id", {})
    if isinstance(id_origem, dict):
        id_origem = id_origem.get("$oid", "")
    id_origem = str(id_origem or payload_comando.get("id", ""))
    valor = payload_comando.get("value", {})
    tipo = valor.get("type") if isinstance(valor, dict) else capacidade
    payload = valor.get("payload", valor) if isinstance(valor, dict) else {"value": valor}

    dispositivo = DispositivoEsp32.objects.select_related("no").filter(interscity_uuid=uuid).first()
    no = dispositivo.no if dispositivo else NoBorda.objects.filter(interscity_uuid=uuid).first()
    if no is None:
        raise ValidationError({"uuid": "Nenhum recurso AutoPonto está vinculado a esse uuid do Interscity."})

    comando, _ = ComandoBorda.objects.update_or_create(
        origem="interscity",
        id_origem=id_origem,
        defaults={
            "no": no,
            "dispositivo": dispositivo,
            "tipo": tipo or capacidade or "command",
            "payload": payload if isinstance(payload, dict) else {"value": payload},
            "status": ComandoBorda.STATUS_PENDENTE,
            "capacidade": capacidade,
        },
    )
    return comando


build_pull_payload = montar_payload_pull
submit_edge_attendance = receber_presencas_borda
create_command_from_interscity = criar_comando_por_interscity
