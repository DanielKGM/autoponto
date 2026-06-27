import json

from django.conf import settings

from .errors import DomainValidationError


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
    payload = json.dumps([float(valor) for valor in vetor], separators=(",", ":")).encode("utf-8")
    return _fernet().encrypt(payload).decode("ascii")


def descriptografar_vetor(payload) -> list[float]:
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
        raise DomainValidationError("Nao foi possivel descriptografar embedding facial.") from exc
    if not isinstance(dados, list):
        raise DomainValidationError("Embedding facial descriptografado invalido.")
    return [float(valor) for valor in dados]


def ciphertext_para_edge(payload) -> str:
    if isinstance(payload, str):
        return payload
    return criptografar_vetor(descriptografar_vetor(payload))
