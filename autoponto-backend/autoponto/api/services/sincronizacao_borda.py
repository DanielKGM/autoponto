from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from api.models import (
    Aula,
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


ENTIDADES_SYNC = ("salas", "dispositivos", "aulas", "alunos", "matriculas_aula", "embeddings_faciais")


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


def _iso(valor):
    return valor.isoformat().replace("+00:00", "Z")


def _max_cursor(itens) -> str:
    datas = [item.atualizado_em for item in itens if getattr(item, "atualizado_em", None)]
    return _iso(max(datas) if datas else timezone.now())


def _validar_no(no: NoBorda, identificador: str | None):
    if identificador and identificador not in {str(no.id), no.codigo}:
        raise ValidationError({"node_id": "Token do no nao corresponde ao node_id solicitado."})


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
    data_sync = timezone.localdate()
    dispositivos = _dispositivos_do_no(no)
    dispositivos_ativos = [dispositivo for dispositivo in dispositivos if dispositivo.ativo and dispositivo.sala_id]
    salas_do_no = [dispositivo.sala for dispositivo in dispositivos if dispositivo.sala_id]
    salas_ativas = [sala for sala in salas_do_no if isinstance(sala, Sala) and sala.ativo]

    aulas = []
    for sala in salas_ativas:
        aulas.extend(listar_aulas_do_dia(data_sync, sala=sala))
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
        EmbeddingFacial.objects.select_related("aluno").filter(
            aluno_id__in=aluno_ids,
            ativo=True,
            status="ATIVO",
        )
    )

    aulas_por_turma = {}
    for aula in aulas_disponiveis:
        aulas_por_turma.setdefault(aula.horario.turma_id, []).append(aula)

    dados = {
        "salas": [
            {"id": str(sala.id), "nome": sala.nome}
            for sala in sorted(set(salas_ativas), key=lambda item: item.nome)
        ],
        "dispositivos": [
            {
                "id": dispositivo.codigo,
                "sala_id": str(dispositivo.sala_id),
                "ativo": dispositivo.ativo,
                "interscity_uuid": dispositivo.interscity_uuid,
            }
            for dispositivo in dispositivos_ativos
        ],
        "aulas": [
            {
                "id": str(aula.id),
                "nome": f"{aula.horario.turma.disciplina.nome} - {aula.horario.turma.codigo}",
                "sala_id": str(aula.horario.sala_id),
                "inicio": _iso(aula.inicio),
                "fim": _iso(aula.fim),
                "status": aula.status,
            }
            for aula in aulas_disponiveis
        ],
        "alunos": [
            {
                "id": str(aluno.id),
                "matricula": aluno.matricula,
                "nome": aluno.nome_completo or aluno.username,
            }
            for aluno in alunos
        ],
        "matriculas_aula": [
            {"aula_id": str(aula.id), "aluno_id": str(matricula.aluno_id)}
            for matricula in matriculas
            for aula in aulas_por_turma.get(matricula.turma_id, [])
        ],
        "embeddings_faciais": [
            {"id": str(embedding.id), "aluno_id": str(embedding.aluno_id), "vetor": embedding.vetor}
            for embedding in embeddings
        ],
    }

    dispositivos_inativos = _filtrar_alterados(
        DispositivoEsp32.objects.filter(no=no, ativo=False),
        cursors.get("dispositivos"),
    )
    salas_inativas = _filtrar_alterados(
        Sala.objects.filter(id__in=[sala.id for sala in salas_do_no if sala], ativo=False),
        cursors.get("salas"),
    )
    aulas_canceladas = _filtrar_alterados(
        Aula.objects.filter(
            horario__sala_id__in=[sala.id for sala in salas_do_no if sala],
            data=data_sync,
        ).filter(
            Q(status__in=[Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA])
            | Q(horario__ativo=False)
            | Q(horario__turma__ativo=False)
        ),
        cursors.get("aulas"),
    )
    matriculas_inativas = _filtrar_alterados(
        MatriculaTurma.objects.filter(turma_id__in=turmas, ativo=False),
        cursors.get("matriculas_aula"),
    )
    alunos_inativos = _filtrar_alterados(
        Usuario.objects.filter(id__in=aluno_ids, is_active=False),
        cursors.get("alunos"),
    )
    embeddings_inativos = _filtrar_alterados(
        EmbeddingFacial.objects.filter(aluno_id__in=aluno_ids).filter(Q(ativo=False) | ~Q(status="ATIVO")),
        cursors.get("embeddings_faciais"),
    )

    deletados = {
        "salas": [str(sala.id) for sala in salas_inativas],
        "dispositivos": [dispositivo.codigo for dispositivo in dispositivos_inativos],
        "aulas": [str(aula.id) for aula in aulas_canceladas],
        "alunos": [str(aluno.id) for aluno in alunos_inativos],
        "matriculas_aula": [
            {"aula_id": str(aula.id), "aluno_id": str(matricula.aluno_id)}
            for matricula in matriculas_inativas
            for aula in aulas_por_turma.get(matricula.turma_id, [])
        ],
        "embeddings_faciais": [str(embedding.id) for embedding in embeddings_inativos],
    }

    return {
        "data": dados,
        "deleted": deletados,
        "cursors": {
            "salas": _max_cursor([sala for sala in salas_do_no if sala]),
            "dispositivos": _max_cursor(dispositivos),
            "aulas": _max_cursor(aulas),
            "alunos": _max_cursor(alunos),
            "matriculas_aula": _max_cursor(matriculas),
            "embeddings_faciais": _max_cursor(embeddings),
        },
    }


def _parsear_data_hora(valor: str):
    try:
        parseado = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValidationError({"datetime": "Informe uma data e hora ISO valida."}) from exc
    if parseado.tzinfo is None:
        return timezone.make_aware(parseado)
    return parseado


def receber_presencas_borda(no: NoBorda, payload: dict) -> dict:
    _validar_no(no, payload.get("node_id"))

    ids_sincronizados = []
    eventos = payload.get("eventos", [])
    if not isinstance(eventos, list):
        raise ValidationError({"eventos": "Informe uma lista de eventos de presenca."})
    for evento in eventos:
        id_evento = evento.get("id")
        if not id_evento:
            raise ValidationError({"eventos": "Todo evento deve incluir um id."})
        ids_sincronizados.append(_receber_evento_borda(no, evento))
    return {"synced_ids": ids_sincronizados}


@transaction.atomic
def _receber_evento_borda(no: NoBorda, evento: dict) -> str:
    id_evento = evento["id"]
    existente = EventoReconhecimento.objects.filter(id_evento_origem=id_evento).first()
    if existente:
        return id_evento

    try:
        dispositivo = DispositivoEsp32.objects.get(codigo=evento["dispositivo_id"], no=no, ativo=True)
        aula = Aula.objects.select_related("horario", "horario__turma").get(id=evento["aula_id"])
        aluno = Usuario.objects.get(id=evento["aluno_id"], papel=PapelUsuario.ALUNO, is_active=True)
    except KeyError as exc:
        raise ValidationError({"eventos": "Evento deve incluir aluno_id, aula_id, dispositivo_id e reconhecido_em."}) from exc
    except (DispositivoEsp32.DoesNotExist, Aula.DoesNotExist, Usuario.DoesNotExist) as exc:
        raise ValidationError({"eventos": "Evento referencia no, dispositivo, aula ou aluno desconhecido."}) from exc

    if aula.horario.sala_id != dispositivo.sala_id:
        raise ValidationError({"eventos": "A aula do evento nao pertence a sala do dispositivo."})

    matriculado = MatriculaTurma.objects.filter(turma=aula.horario.turma, aluno=aluno, ativo=True).exists()
    if not matriculado:
        raise ValidationError({"eventos": "Aluno nao esta matriculado na aula enviada."})

    reconhecido_em = _parsear_data_hora(evento["reconhecido_em"])

    if aula.status in {Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA}:
        raise ValidationError({"eventos": "A chamada da aula esta fechada ou cancelada."})
    if reconhecido_em < aula.inicio or reconhecido_em > aula.fim:
        raise ValidationError({"eventos": "Evento fora da duracao da aula."})

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
