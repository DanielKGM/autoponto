import base64
import json
import struct
import zlib
from dataclasses import dataclass
from typing import Iterable

from django.conf import settings

from .crypto_biometria import descriptografar_vetor
from .errors import DomainValidationError


INDEX_KEY = "face:embeddings"
KEY_PREFIX = "face:embedding:"
_LOCMEM: dict[str, str | set[str]] = {}


@dataclass(frozen=True)
class EmbeddingCacheItem:
    aluno_id: str
    vetor: list[float]


def _key(embedding_id: str) -> str:
    return f"{KEY_PREFIX}{embedding_id}"


def _redis():
    url = getattr(settings, "FACE_EMBEDDING_CACHE_URL", "")
    if url == "locmem://":
        return None
    if not url:
        raise DomainValidationError("Configure FACE_EMBEDDING_CACHE_URL para validar biometria facial.")
    try:
        import redis
    except ImportError as exc:
        raise DomainValidationError("Instale redis para usar cache de biometria facial.") from exc
    try:
        client = redis.Redis.from_url(
            url,
            password=getattr(settings, "FACE_EMBEDDING_CACHE_PASSWORD", "") or None,
            socket_connect_timeout=2,
            socket_timeout=5,
            decode_responses=True,
        )
        client.ping()
        return client
    except Exception as exc:
        raise DomainValidationError("Cache Redis de biometria indisponivel.") from exc


def _queryset_ativos():
    from api.models import EmbeddingFacial

    return EmbeddingFacial.objects.filter(
        ativo=True,
        status=EmbeddingFacial.STATUS_ATIVO,
    ).order_by("id")


def _ids_ativos() -> set[str]:
    return {str(embedding_id) for embedding_id in _queryset_ativos().values_list("id", flat=True)}


def _buscar_embedding(embedding_id: str):
    return _queryset_ativos().filter(id=embedding_id).first()


def _compactar(vetor: list[float]) -> str:
    bruto = struct.pack(f"<{len(vetor)}f", *[float(valor) for valor in vetor])
    return base64.b64encode(zlib.compress(bruto)).decode("ascii")


def _descompactar(valor: str) -> list[float]:
    bruto = zlib.decompress(base64.b64decode(valor.encode("ascii")))
    if not bruto:
        return []
    return list(struct.unpack(f"<{len(bruto) // 4}f", bruto))


def _payload(embedding) -> str:
    return json.dumps(
        {
            "aluno_id": str(embedding.aluno_id),
            "vetor": _compactar(descriptografar_vetor(embedding.vetor)),
        },
        separators=(",", ":"),
    )


def _item(payload: str) -> EmbeddingCacheItem:
    dados = json.loads(payload)
    return EmbeddingCacheItem(
        aluno_id=str(dados["aluno_id"]),
        vetor=_descompactar(dados["vetor"]),
    )


def _locmem_salvar(embedding) -> None:
    embedding_id = str(embedding.id)
    _LOCMEM[_key(embedding_id)] = _payload(embedding)
    index = _LOCMEM.setdefault(INDEX_KEY, set())
    assert isinstance(index, set)
    index.add(embedding_id)


def _locmem_remover(ids: Iterable[str]) -> None:
    index = _LOCMEM.setdefault(INDEX_KEY, set())
    assert isinstance(index, set)
    for embedding_id in ids:
        _LOCMEM.pop(_key(str(embedding_id)), None)
        index.discard(str(embedding_id))


def salvar_embedding(embedding) -> None:
    client = _redis()
    if client is None:
        _locmem_salvar(embedding)
        return
    embedding_id = str(embedding.id)
    client.set(_key(embedding_id), _payload(embedding))
    client.sadd(INDEX_KEY, embedding_id)


def remover_embeddings(ids: Iterable[str]) -> None:
    ids = [str(embedding_id) for embedding_id in ids]
    if not ids:
        return
    client = _redis()
    if client is None:
        _locmem_remover(ids)
        return
    client.delete(*[_key(embedding_id) for embedding_id in ids])
    client.srem(INDEX_KEY, *ids)


def _sync_index(client, ids_ativos: set[str]) -> set[str]:
    ids_cache = set(_LOCMEM.get(INDEX_KEY, set())) if client is None else set(client.smembers(INDEX_KEY))
    for embedding_id in ids_ativos - ids_cache:
        embedding = _buscar_embedding(embedding_id)
        if embedding:
            salvar_embedding(embedding)
    stale = ids_cache - ids_ativos
    if stale:
        remover_embeddings(stale)
    return ids_ativos


def listar_embeddings_ativos() -> list[EmbeddingCacheItem]:
    client = _redis()
    ids = _sync_index(client, _ids_ativos())
    itens: list[EmbeddingCacheItem] = []
    for embedding_id in sorted(ids):
        payload = _LOCMEM.get(_key(embedding_id)) if client is None else client.get(_key(embedding_id))
        if payload is None:
            embedding = _buscar_embedding(embedding_id)
            if not embedding:
                remover_embeddings([embedding_id])
                continue
            salvar_embedding(embedding)
            payload = _LOCMEM.get(_key(embedding_id)) if client is None else client.get(_key(embedding_id))
        if isinstance(payload, str):
            itens.append(_item(payload))
    return itens


def limpar_locmem_para_testes() -> None:
    _LOCMEM.clear()
