import json
from time import perf_counter

from django.conf import settings

from .errors import DomainValidationError
from .tcc_metricas import registrar_tempo


def _fernet():
    chave = getattr(settings, "FACE_EMBEDDING_ENCRYPTION_KEY", "")
    if not chave:
        raise DomainValidationError("Configure FACE_EMBEDDING_ENCRYPTION_KEY para usar biometria facial.")
    try:
        from cryptography.fernet import Fernet
    except ImportError as exc:
        raise DomainValidationError("Instale cryptography para usar biometria facial criptografada.") from exc
    try:
        return Fernet(chave.encode("ascii"))
    except (TypeError, ValueError) as exc:
        raise DomainValidationError("FACE_EMBEDDING_ENCRYPTION_KEY deve ser uma chave Fernet valida.") from exc


def criptografar_vetor(vetor: list[float]) -> str:
    inicio = perf_counter()
    try:
        payload = json.dumps([float(valor) for valor in vetor], separators=(",", ":")).encode("utf-8")
        resultado = _fernet().encrypt(payload).decode("ascii")
    except Exception as exc:
        registrar_tempo(
            "embedding_criptografia_ms",
            (perf_counter() - inicio) * 1000,
            servico="servidor-principal",
            status="falha",
            origem="criptografar_vetor",
            detalhes={"dimensoes": len(vetor) if vetor else 0, "erro": exc.__class__.__name__},
        )
        raise

    registrar_tempo(
        "embedding_criptografia_ms",
        (perf_counter() - inicio) * 1000,
        servico="servidor-principal",
        origem="criptografar_vetor",
        detalhes={"dimensoes": len(vetor) if vetor else 0},
    )
    return resultado


def descriptografar_vetor(payload) -> list[float]:
    inicio = perf_counter()
    medir = bool(payload) and not isinstance(payload, list)
    if not payload:
        return []
    if isinstance(payload, list):
        return [float(valor) for valor in payload]
    if isinstance(payload, dict):
        payload = payload.get("ciphertext", "")
    if not isinstance(payload, str):
        raise DomainValidationError("Payload de embedding facial invalido.")
    if not payload:
        return []
    try:
        bruto = _fernet().decrypt(payload.encode("ascii"))
        dados = json.loads(bruto.decode("utf-8"))
    except Exception as exc:
        if medir:
            registrar_tempo(
                "embedding_descriptografia_ms",
                (perf_counter() - inicio) * 1000,
                servico="servidor-principal",
                status="falha",
                origem="descriptografar_vetor",
                detalhes={"erro": exc.__class__.__name__},
            )
        raise DomainValidationError("Nao foi possivel descriptografar embedding facial.") from exc
    try:
        if not isinstance(dados, list):
            raise DomainValidationError("Embedding facial descriptografado invalido.")
        resultado = [float(valor) for valor in dados]
    except Exception as exc:
        if medir:
            registrar_tempo(
                "embedding_descriptografia_ms",
                (perf_counter() - inicio) * 1000,
                servico="servidor-principal",
                status="falha",
                origem="descriptografar_vetor",
                detalhes={"erro": exc.__class__.__name__},
            )
        raise
    if medir:
        registrar_tempo(
            "embedding_descriptografia_ms",
            (perf_counter() - inicio) * 1000,
            servico="servidor-principal",
            origem="descriptografar_vetor",
            detalhes={"dimensoes": len(resultado)},
        )
    return resultado


def ciphertext_para_edge(payload) -> str:
    if isinstance(payload, str):
        return payload
    return criptografar_vetor(descriptografar_vetor(payload))
