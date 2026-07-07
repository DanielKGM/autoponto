from datetime import datetime
from decimal import Decimal
from time import perf_counter

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
from api.selectors.aulas import com_status_aula, status_aula
from api.services.crypto_biometria import ciphertext_para_edge
from api.services.tcc_metricas import registrar_tempo, registrar_valor


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
    agora = timezone.now()
    queryset = (
        Aula.objects.select_related("turma", "turma__disciplina", "sala")
        .filter(
            data=data_sync,
            sala__in=_salas_do_no(no).filter(ativo=True),
            turma__ativo=True,
            fim__gt=agora,
            cancelada_em__isnull=True,
            fechada_em__isnull=True,
        )
        .order_by("inicio", "id")
        .distinct()
    )
    return com_status_aula(queryset, agora=agora)


def _matriculas_ativas_das_aulas(aulas):
    return MatriculaTurma.objects.select_related("aluno").filter(
        turma_id__in=aulas.values("turma_id"),
        ativo=True,
        aluno__papel=PapelUsuario.ALUNO,
        aluno__is_active=True,
    )


def _nome_aluno(aluno: Usuario) -> str:
    return aluno.nome_completo or aluno.username


def _embedding_face_worker(vetor) -> str:
    return ciphertext_para_edge(vetor)


def _cache_redis_snapshot(no: NoBorda, data_sync) -> dict:
    # dispositivos que têm salas e pertencem ao nó
    dispositivos = (
        DispositivoEsp32.objects.select_related("sala")
        .filter(no=no, ativo=True, sala__isnull=False)
        .order_by("codigo")
    )

    # aulas de interesse para esse nó (nas salas do nó, salas e turmas ativas, planejadas)
    aulas = _aulas_disponiveis_do_no(no, data_sync)

    # recuperar matrículas das aulas
    # matrículas e alunos ativos
    matriculas = _matriculas_ativas_das_aulas(aulas)

    # alunos das matrículas anteriormente filtradas
    alunos = Usuario.objects.filter(id__in=matriculas.values("aluno_id")).order_by(
        "username", "id"
    )

    # embeddings ativos dos alunos
    embeddings = EmbeddingFacial.objects.filter(
        aluno_id__in=matriculas.values("aluno_id"),
        ativo=True,
        status=EmbeddingFacial.STATUS_ATIVO,
    ).order_by("aluno_id", "id")

    # {aula1.id: [dict, dict, ...], aula2.id: [dict, dict, ...], (...)}
    alunos_por_aula = {str(aula.id): [] for aula in aulas}

    aulas_por_sala: dict[str, list[dict]] = {}
    alunos_por_turma: dict[str, list[str]] = {}

    for matricula in matriculas.order_by("aluno__username", "id").distinct():
        alunos_por_turma.setdefault(str(matricula.turma_id), []).append(
            str(matricula.aluno_id)
        )

    for aula in aulas:
        aula_payload = {
            "id": str(aula.id),
            "nome": str(aula.turma.disciplina.nome),
            "turma_id": str(aula.turma_id),
            "sala_id": str(aula.sala_id),
            "inicio": _iso(aula.inicio),
            "fim": _iso(aula.fim),
            "status": status_aula(aula),
        }
        aulas_por_sala.setdefault(str(aula.sala_id), []).append(aula_payload)
        alunos_por_aula[str(aula.id)] = alunos_por_turma.get(str(aula.turma_id), [])

    # cachê em NOSQL para maior performance em REDIS, utilizados no EdgeNode
    return {
        "dispositivos_por_codigo": {
            dispositivo.codigo: {
                "dispositivo_id": str(dispositivo.id),
                "dispositivo_codigo": dispositivo.codigo,
                "sala_id": str(dispositivo.sala_id),
                "ativo": dispositivo.ativo,
                "interscity_uuid": dispositivo.interscity_uuid,
            }
            for dispositivo in dispositivos
        },
        "aulas_por_sala": aulas_por_sala,
        "alunos_por_aula": alunos_por_aula,
        "alunos_por_id": {
            str(aluno.id): {"nome": _nome_aluno(aluno)} for aluno in alunos.distinct()
        },
        "embeddings_faciais": {
            str(embedding.id): {
                "alunoId": str(embedding.aluno_id),
                "embedding_encrypted": _embedding_face_worker(embedding.vetor),
            }
            for embedding in embeddings.distinct()
        },
    }


def montar_payload_pull(no: NoBorda, query_params) -> dict:
    inicio = perf_counter()
    try:
        _validar_no(no, query_params.get("node_id"))
        data_sync = timezone.localdate()
        synced_at = timezone.now()
        payload = {
            "snapshot_data": data_sync.isoformat(),
            "synced_at": _iso(synced_at),
            "cache_redis": _cache_redis_snapshot(no, data_sync),
        }
    except Exception as exc:
        registrar_tempo(
            "edge_snapshot_total_ms",
            (perf_counter() - inicio) * 1000,
            servico="servidor-principal",
            status="falha",
            origem="montar_payload_pull",
            detalhes={"erro": exc.__class__.__name__},
        )
        raise

    cache = payload["cache_redis"]
    dispositivos_total = len(cache["dispositivos_por_codigo"])
    aulas_total = sum(len(aulas) for aulas in cache["aulas_por_sala"].values())
    embeddings_total = len(cache["embeddings_faciais"])
    detalhes = {
        "no": no.codigo,
        "dispositivos": dispositivos_total,
        "aulas": aulas_total,
        "embeddings": embeddings_total,
    }
    registrar_tempo(
        "edge_snapshot_total_ms",
        (perf_counter() - inicio) * 1000,
        servico="servidor-principal",
        origem="montar_payload_pull",
        detalhes=detalhes,
    )
    registrar_valor(
        "edge_snapshot_dispositivos_total",
        dispositivos_total,
        unidade="contagem",
        servico="servidor-principal",
        origem="montar_payload_pull",
        detalhes=detalhes,
    )
    registrar_valor(
        "edge_snapshot_aulas_total",
        aulas_total,
        unidade="contagem",
        servico="servidor-principal",
        origem="montar_payload_pull",
        detalhes=detalhes,
    )
    registrar_valor(
        "edge_snapshot_embeddings_total",
        embeddings_total,
        unidade="contagem",
        servico="servidor-principal",
        origem="montar_payload_pull",
        detalhes=detalhes,
    )
    return payload


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
    inicio = perf_counter()
    eventos = payload.get("eventos", [])
    eventos_total = len(eventos) if isinstance(eventos, list) else 0
    registrar_valor(
        "edge_attendance_eventos_total",
        eventos_total,
        unidade="contagem",
        servico="servidor-principal",
        origem="receber_presencas_borda",
        detalhes={"no": no.codigo},
    )

    try:
        _validar_no(no, payload.get("node_id"))

        ids_sincronizados = []
        if not isinstance(eventos, list):
            raise ValidationError({"eventos": "Informe uma lista de eventos de presenca."})
        for evento in eventos:
            id_evento = evento.get("id")
            if not id_evento:
                raise ValidationError({"eventos": "Todo evento deve incluir um id."})
            ids_sincronizados.append(_receber_evento_borda(no, evento))
    except Exception as exc:
        registrar_tempo(
            "edge_attendance_total_ms",
            (perf_counter() - inicio) * 1000,
            servico="servidor-principal",
            status="falha",
            origem="receber_presencas_borda",
            detalhes={
                "no": no.codigo,
                "eventos": eventos_total,
                "erro": exc.__class__.__name__,
            },
        )
        raise

    registrar_tempo(
        "edge_attendance_total_ms",
        (perf_counter() - inicio) * 1000,
        servico="servidor-principal",
        origem="receber_presencas_borda",
        detalhes={
            "no": no.codigo,
            "eventos": eventos_total,
            "sincronizados": len(ids_sincronizados),
        },
    )
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

    if aula.cancelada_em or aula.fechada_em:
        raise ValidationError(
            {"eventos": "A chamada da aula esta fechada ou cancelada."}
        )
    if reconhecido_em < aula.inicio or reconhecido_em >= aula.fim:
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

    embedding = (
        EmbeddingFacial.objects.filter(
            aluno=aluno,
            ativo=True,
            status=EmbeddingFacial.STATUS_ATIVO,
        )
        .order_by("-criado_em")
        .first()
    )
    EventoReconhecimento.objects.create(
        id_evento_origem=id_evento,
        dispositivo=dispositivo,
        aula=aula,
        aluno_candidato=aluno,
        embedding=embedding,
        confianca=Decimal(str(evento.get("score", 0))).quantize(Decimal("0.0001")),
        reconhecido=True,
        ocorrido_em=reconhecido_em,
    )
    return id_evento
