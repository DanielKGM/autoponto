from datetime import datetime
from decimal import Decimal

import msgpack
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from api.models import (
    Aula,
    DispositivoEsp32,
    EmbeddingFacial,
    EventoReconhecimento,
    EventoSincronizacaoBorda,
    MatriculaTurma,
    NoBorda,
    PapelUsuario,
    RegistroPresenca,
    Sala,
    Usuario,
)

ENTIDADES_SYNC = (
    "salas",
    "dispositivos",
    "aulas",
    "alunos",
    "matriculas_turma",
    "embeddings_faciais",
)


def _iso(valor):
    return valor.isoformat().replace("+00:00", "Z")


def _payload_vazio() -> dict:
    return {entidade: [] for entidade in ENTIDADES_SYNC}


def _validar_no(no: NoBorda, identificador: str | None):
    if identificador and identificador not in {str(no.id), no.codigo}:
        raise ValidationError(
            {"node_id": "Token do no nao corresponde ao node_id solicitado."}
        )


def _cursors_no_marco(marco) -> dict:
    return {entidade: _iso(marco) for entidade in ENTIDADES_SYNC}


def _decodificar_cursors(valor: str) -> dict:
    try:
        cursores = msgpack.unpackb(bytes.fromhex(valor), raw=False)
    except Exception as exc:
        raise ValidationError({"cursors": "Informe cursores msgpack em hexadecimal."}) from exc
    if not isinstance(cursores, dict):
        raise ValidationError({"cursors": "Cursores devem formar um objeto por entidade."})
    return {
        str(entidade): str(cursor)
        for entidade, cursor in cursores.items()
        if entidade in ENTIDADES_SYNC and cursor
    }


def _parsear_cursor_data(entidade: str, valor: str):
    try:
        parseado = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValidationError({entidade: "Cursor deve ser uma data ISO valida."}) from exc
    if parseado.tzinfo is None:
        return timezone.make_aware(parseado)
    return parseado


def _salas_do_no(no: NoBorda):
    return Sala.objects.filter(dispositivos__no=no).distinct()


def _aulas_disponiveis_do_no(no: NoBorda, data_sync):
    return (
        Aula.objects.select_related("turma", "turma__disciplina", "sala")
        .filter(
            data=data_sync,
            sala__in=_salas_do_no(no).filter(ativo=True),
            turma__ativo=True,
        )
        .exclude(status__in=[Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA])
        .order_by("inicio", "id")
        .distinct()
    )


def _matriculas_ativas_das_aulas(aulas):
    return MatriculaTurma.objects.select_related("aluno").filter(
        turma_id__in=aulas.values("turma_id"),
        ativo=True,
        aluno__papel=PapelUsuario.ALUNO,
        aluno__is_active=True,
    )


def _serializar_sala(sala: Sala) -> dict:
    return {"id": str(sala.id), "nome": sala.nome}


def _serializar_dispositivo(dispositivo: DispositivoEsp32) -> dict:
    return {
        "id": str(dispositivo.id),
        "codigo": dispositivo.codigo,
        "sala_id": str(dispositivo.sala_id),
        "ativo": dispositivo.ativo,
        "interscity_uuid": dispositivo.interscity_uuid,
    }


def _serializar_aula(aula: Aula) -> dict:
    return {
        "id": str(aula.id),
        "nome": f"{aula.turma.disciplina.nome} - {aula.turma.codigo}",
        "turma_id": str(aula.turma_id),
        "sala_id": str(aula.sala_id),
        "inicio": _iso(aula.inicio),
        "fim": _iso(aula.fim),
        "status": aula.status,
    }


def _serializar_aluno(aluno: Usuario) -> dict:
    return {
        "id": str(aluno.id),
        "matricula": aluno.matricula,
        "nome": aluno.nome_completo or aluno.username,
    }


def _serializar_embedding(embedding: EmbeddingFacial) -> dict:
    return {
        "id": str(embedding.id),
        "aluno_id": str(embedding.aluno_id),
        "vetor": embedding.vetor,
    }


def _serializar_matricula_turma(matricula: MatriculaTurma) -> dict:
    return {
        "id": str(matricula.id),
        "turma_id": str(matricula.turma_id),
        "aluno_id": str(matricula.aluno_id),
    }


def _payload_completo(no: NoBorda, data_sync) -> dict:
    dispositivos = (
        DispositivoEsp32.objects.select_related("sala")
        .filter(no=no, ativo=True, sala__isnull=False)
        .order_by("codigo")
    )
    salas = _salas_do_no(no).filter(ativo=True).order_by("nome", "id")
    aulas = _aulas_disponiveis_do_no(no, data_sync)
    matriculas = _matriculas_ativas_das_aulas(aulas)
    alunos = Usuario.objects.filter(id__in=matriculas.values("aluno_id")).order_by(
        "username", "id"
    )
    embeddings = EmbeddingFacial.objects.filter(
        aluno_id__in=matriculas.values("aluno_id"),
        ativo=True,
        status="ATIVO",
    ).order_by("aluno_id", "id")

    return {
        "salas": [_serializar_sala(sala) for sala in salas.distinct()],
        "dispositivos": [
            _serializar_dispositivo(dispositivo) for dispositivo in dispositivos
        ],
        "aulas": [_serializar_aula(aula) for aula in aulas],
        "alunos": [_serializar_aluno(aluno) for aluno in alunos.distinct()],
        "matriculas_turma": [
            _serializar_matricula_turma(matricula)
            for matricula in matriculas.order_by("aluno__username", "id").distinct()
        ],
        "embeddings_faciais": [
            _serializar_embedding(embedding) for embedding in embeddings.distinct()
        ],
    }


def _adicionar(dados: dict, entidade: str, identificador, payload: dict):
    dados[entidade][str(identificador)] = payload


def _deletar(dados: dict, deletados: dict, entidade: str, identificador):
    identificador = str(identificador)
    dados[entidade].pop(identificador, None)
    deletados[entidade].add(identificador)


def _adicionar_sala(no: NoBorda, dados: dict, sala_id):
    sala = _salas_do_no(no).filter(id=sala_id, ativo=True).first()
    if sala:
        _adicionar(dados, "salas", sala.id, _serializar_sala(sala))


def _adicionar_aluno_e_embedding(dados: dict, aluno: Usuario):
    _adicionar(dados, "alunos", aluno.id, _serializar_aluno(aluno))
    for embedding in EmbeddingFacial.objects.filter(
        aluno=aluno,
        ativo=True,
        status="ATIVO",
    ).order_by("id"):
        _adicionar(
            dados,
            "embeddings_faciais",
            embedding.id,
            _serializar_embedding(embedding),
        )


def _adicionar_matricula_turma(dados: dict, matricula: MatriculaTurma):
    _adicionar(
        dados,
        "matriculas_turma",
        matricula.id,
        _serializar_matricula_turma(matricula),
    )
    _adicionar_aluno_e_embedding(dados, matricula.aluno)


def _adicionar_matriculas_da_turma(dados: dict, turma_id):
    matriculas = MatriculaTurma.objects.select_related("aluno").filter(
        turma_id=turma_id,
        ativo=True,
        aluno__papel=PapelUsuario.ALUNO,
        aluno__is_active=True,
    )
    for matricula in matriculas:
        _adicionar_matricula_turma(dados, matricula)


def _adicionar_aulas_da_turma_no(no: NoBorda, dados: dict, turma_id, data_sync):
    for aula in _aulas_disponiveis_do_no(no, data_sync).filter(turma_id=turma_id):
        _adicionar(dados, "aulas", aula.id, _serializar_aula(aula))
        _adicionar_sala(no, dados, aula.sala_id)


def _aplicar_upsert(no: NoBorda, dados: dict, deletados: dict, evento, data_sync):
    entidade = evento.entidade
    identificador = evento.identificador

    if entidade == EventoSincronizacaoBorda.Entidade.SALAS:
        sala = _salas_do_no(no).filter(id=identificador, ativo=True).first()
        if sala:
            _adicionar(dados, "salas", sala.id, _serializar_sala(sala))
        return

    if entidade == EventoSincronizacaoBorda.Entidade.DISPOSITIVOS:
        dispositivo = (
            DispositivoEsp32.objects.select_related("sala")
            .filter(id=identificador, no=no, ativo=True, sala__isnull=False)
            .first()
        )
        if dispositivo:
            _adicionar(
                dados,
                "dispositivos",
                dispositivo.id,
                _serializar_dispositivo(dispositivo),
            )
            _adicionar_sala(no, dados, dispositivo.sala_id)
        return

    if entidade == EventoSincronizacaoBorda.Entidade.AULAS:
        aula = _aulas_disponiveis_do_no(no, data_sync).filter(id=identificador).first()
        if aula:
            _adicionar(dados, "aulas", aula.id, _serializar_aula(aula))
            _adicionar_sala(no, dados, aula.sala_id)
            _adicionar_matriculas_da_turma(dados, aula.turma_id)
        else:
            _deletar(dados, deletados, "aulas", identificador)
        return

    if entidade == EventoSincronizacaoBorda.Entidade.MATRICULAS_TURMA:
        matricula = (
            MatriculaTurma.objects.select_related("aluno")
            .filter(
                id=identificador,
                ativo=True,
                aluno__papel=PapelUsuario.ALUNO,
                aluno__is_active=True,
            )
            .first()
        )
        if (
            matricula
            and _aulas_disponiveis_do_no(no, data_sync)
            .filter(turma=matricula.turma)
            .exists()
        ):
            _adicionar_matricula_turma(dados, matricula)
            _adicionar_aulas_da_turma_no(no, dados, matricula.turma_id, data_sync)
        else:
            _deletar(dados, deletados, "matriculas_turma", identificador)
        return

    if entidade == EventoSincronizacaoBorda.Entidade.ALUNOS:
        aluno = Usuario.objects.filter(
            id=identificador,
            papel=PapelUsuario.ALUNO,
            is_active=True,
            matriculas_turma__turma__aulas__in=_aulas_disponiveis_do_no(no, data_sync),
        ).first()
        if aluno:
            _adicionar_aluno_e_embedding(dados, aluno)
        return

    if entidade == EventoSincronizacaoBorda.Entidade.EMBEDDINGS_FACIAIS:
        embedding = (
            EmbeddingFacial.objects.select_related("aluno")
            .filter(
                id=identificador,
                ativo=True,
                status="ATIVO",
                aluno__is_active=True,
                aluno__matriculas_turma__turma__aulas__in=_aulas_disponiveis_do_no(
                    no, data_sync
                ),
            )
            .first()
        )
        if embedding:
            _adicionar_aluno_e_embedding(dados, embedding.aluno)
        else:
            _deletar(dados, deletados, "embeddings_faciais", identificador)


def _payload_incremental(
    no: NoBorda,
    cursores: dict,
    data_sync,
    marco_cursor,
) -> tuple[dict, dict]:
    dados = {entidade: {} for entidade in ENTIDADES_SYNC}
    deletados = {entidade: set() for entidade in ENTIDADES_SYNC}
    cursores_parseados = {
        entidade: _parsear_cursor_data(entidade, cursores[entidade])
        for entidade in ENTIDADES_SYNC
    }
    menor_cursor = min(cursores_parseados.values())
    eventos_finais = {}

    for evento in EventoSincronizacaoBorda.objects.filter(
        criado_em__gt=menor_cursor,
        criado_em__lte=marco_cursor,
    ).order_by("id"):
        if evento.criado_em <= cursores_parseados[evento.entidade]:
            continue
        eventos_finais[(evento.entidade, evento.identificador)] = evento

    for evento in sorted(eventos_finais.values(), key=lambda item: item.id):
        if evento.acao == EventoSincronizacaoBorda.Acao.DELETE:
            _deletar(dados, deletados, evento.entidade, evento.identificador)
        else:
            _aplicar_upsert(no, dados, deletados, evento, data_sync)

    return (
        {entidade: list(valores.values()) for entidade, valores in dados.items()},
        {entidade: sorted(valores) for entidade, valores in deletados.items()},
    )


def montar_payload_pull(no: NoBorda, query_params) -> dict:
    _validar_no(no, query_params.get("node_id"))
    data_sync = timezone.localdate()
    marco_cursor = timezone.now()

    parametro_full = query_params.get("full")
    if parametro_full not in (None, "") and str(parametro_full).lower() != "true":
        raise ValidationError({"full": "Use full=true para solicitar sincronizacao completa."})

    if str(parametro_full).lower() == "true":
        return {
            "full": True,
            "full_required": False,
            "data": _payload_completo(no, data_sync),
            "deleted": _payload_vazio(),
            "cursors": _cursors_no_marco(marco_cursor),
        }

    valor_cursors = query_params.get("cursors")
    if valor_cursors in (None, ""):
        raise ValidationError({"cursors": "Informe cursors ou full=true."})

    cursores = _decodificar_cursors(valor_cursors)
    if set(cursores) != set(ENTIDADES_SYNC):
        return {
            "full": True,
            "full_required": False,
            "data": _payload_completo(no, data_sync),
            "deleted": _payload_vazio(),
            "cursors": _cursors_no_marco(marco_cursor),
        }

    dados, deletados = _payload_incremental(no, cursores, data_sync, marco_cursor)
    return {
        "full": False,
        "full_required": False,
        "data": dados,
        "deleted": deletados,
        "cursors": _cursors_no_marco(marco_cursor),
    }


def _parsear_data_hora(valor: str):
    try:
        parseado = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            {"datetime": "Informe uma data e hora ISO valida."}
        ) from exc
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
        dispositivo = DispositivoEsp32.objects.get(
            id=evento["dispositivo_id"], no=no, ativo=True
        )
        aula = Aula.objects.select_related("turma", "sala").get(id=evento["aula_id"])
        aluno = Usuario.objects.get(
            id=evento["aluno_id"], papel=PapelUsuario.ALUNO, is_active=True
        )
    except KeyError as exc:
        raise ValidationError(
            {
                "eventos": "Evento deve incluir aluno_id, aula_id, dispositivo_id e reconhecido_em."
            }
        ) from exc
    except (
        ValueError,
        DjangoValidationError,
        DispositivoEsp32.DoesNotExist,
        Aula.DoesNotExist,
        Usuario.DoesNotExist,
    ) as exc:
        raise ValidationError(
            {
                "eventos": "Evento referencia no, dispositivo, aula ou aluno desconhecido."
            }
        ) from exc

    if aula.sala_id != dispositivo.sala_id:
        raise ValidationError(
            {"eventos": "A aula do evento nao pertence a sala do dispositivo."}
        )

    matriculado = MatriculaTurma.objects.filter(
        turma=aula.turma, aluno=aluno, ativo=True
    ).exists()
    if not matriculado:
        raise ValidationError(
            {"eventos": "Aluno nao esta matriculado na aula enviada."}
        )

    reconhecido_em = _parsear_data_hora(evento["reconhecido_em"])

    if aula.status in {Aula.STATUS_FECHADA, Aula.STATUS_CANCELADA}:
        raise ValidationError(
            {"eventos": "A chamada da aula esta fechada ou cancelada."}
        )
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
