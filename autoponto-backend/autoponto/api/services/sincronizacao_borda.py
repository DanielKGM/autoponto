from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
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
from api.serializers.edge import EDGE_ENTIDADES, EDGE_SERIALIZERS

ENTIDADES_SYNC = EDGE_ENTIDADES


def _iso(valor):
    return valor.isoformat().replace("+00:00", "Z")


def _validar_no(no: NoBorda, identificador: str | None):
    if identificador and identificador not in {str(no.id), no.codigo}:
        raise ValidationError(
            {"node_id": "Token do no nao corresponde ao node_id solicitado."}
        )


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


def _serializar(entidade: str, valor, many: bool = False):
    return EDGE_SERIALIZERS[entidade](valor, many=many).data


def _payload_snapshot(no: NoBorda, data_sync) -> dict:
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
        "salas": _serializar("salas", salas.distinct(), many=True),
        "dispositivos": _serializar("dispositivos", dispositivos, many=True),
        "aulas": _serializar("aulas", aulas, many=True),
        "alunos": _serializar("alunos", alunos.distinct(), many=True),
        "matriculas_turma": _serializar(
            "matriculas_turma",
            matriculas.order_by("aluno__username", "id").distinct(),
            many=True,
        ),
        "embeddings_faciais": _serializar(
            "embeddings_faciais",
            embeddings.distinct(),
            many=True,
        ),
    }


def montar_payload_pull(no: NoBorda, query_params) -> dict:
    _validar_no(no, query_params.get("node_id"))
    data_sync = timezone.localdate()
    synced_at = timezone.now()
    return {
        "data": _payload_snapshot(no, data_sync),
        "synced_at": _iso(synced_at),
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
