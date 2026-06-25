import base64
import binascii
from math import sqrt
from pathlib import Path

from django.conf import settings
from django.db import transaction

from api.models import EmbeddingFacial, PapelUsuario, Usuario
from .errors import ConflictError, DomainValidationError

FACE_MAX_CAPTURAS_PADRAO = 5
FACE_MAX_IMAGE_BYTES_PADRAO = 5 * 1024 * 1024


def _formato_imagem(bruto: bytes) -> str | None:
    if bruto.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if bruto.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if len(bruto) >= 12 and bruto[:4] == b"RIFF" and bruto[8:12] == b"WEBP":
        return "WebP"
    return None


def _limite_legivel(limite_bytes: int) -> str:
    if limite_bytes % (1024 * 1024) == 0:
        return f"{limite_bytes // (1024 * 1024)} MB"
    return f"{limite_bytes} bytes"


def validar_capturas_biometricas(capturas: list[str]) -> list[str]:
    if not capturas:
        raise DomainValidationError("Ao menos uma captura é necessária para cadastrar biometria.")

    limite_capturas = int(getattr(settings, "FACE_MAX_CAPTURAS", FACE_MAX_CAPTURAS_PADRAO))
    if len(capturas) > limite_capturas:
        raise DomainValidationError(f"Envie no máximo {limite_capturas} captura(s) para a biometria.")

    limite_bytes = int(getattr(settings, "FACE_MAX_IMAGE_BYTES", FACE_MAX_IMAGE_BYTES_PADRAO))
    for indice, captura in enumerate(capturas, start=1):
        try:
            bruto = base64.b64decode(captura, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise DomainValidationError(f"A captura {indice} não é um base64 válido.") from exc
        if len(bruto) > limite_bytes:
            raise DomainValidationError(f"A captura {indice} excede o limite de {_limite_legivel(limite_bytes)}.")
        if _formato_imagem(bruto) is None:
            raise DomainValidationError(f"A captura {indice} deve ser uma imagem JPEG, PNG ou WebP.")
    return capturas


def _resolver_caminho_modelo(valor: str, nome_variavel: str) -> str:
    if not valor:
        raise DomainValidationError(f"Configure {nome_variavel} com o caminho do modelo ONNX antes de cadastrar biometria.")

    caminho = Path(valor)
    if not caminho.is_absolute():
        caminho = Path(settings.BASE_DIR) / caminho
    if not caminho.exists():
        raise DomainValidationError(f"Modelo ONNX não encontrado em {caminho}. Verifique {nome_variavel}.")
    if not caminho.is_file():
        raise DomainValidationError(f"O caminho configurado em {nome_variavel} não aponta para um arquivo ONNX.")
    return str(caminho)


class GeradorEmbeddingVisao:
    def __init__(self, caminho_modelo_deteccao: str | None = None, caminho_modelo_reconhecimento: str | None = None):
        self.caminho_modelo_deteccao = caminho_modelo_deteccao or getattr(settings, "FACE_DETECT_MODEL_PATH", "")
        self.caminho_modelo_reconhecimento = caminho_modelo_reconhecimento or getattr(settings, "FACE_RECOG_MODEL_PATH", "")

    def gerar_embedding(self, capturas: list[str]) -> tuple[list[float], dict]:
        capturas = validar_capturas_biometricas(capturas)

        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise DomainValidationError("OpenCV e NumPy são necessários para gerar embeddings faciais.") from exc

        caminho_deteccao = _resolver_caminho_modelo(self.caminho_modelo_deteccao, "FACE_DETECT_MODEL_PATH")
        caminho_reconhecimento = _resolver_caminho_modelo(self.caminho_modelo_reconhecimento, "FACE_RECOG_MODEL_PATH")

        detector = cv2.FaceDetectorYN.create(
            caminho_deteccao,
            "",
            (240, 240),
            float(getattr(settings, "FACE_SCORE_THRESHOLD", 0.85)),
            0.3,
            5000,
        )
        reconhecedor = cv2.FaceRecognizerSF.create(caminho_reconhecimento, "")
        vetores = []
        capturas_decodificadas = 0
        quantidade_faces = 0

        limite_pixels = int(getattr(settings, "FACE_MAX_IMAGE_PIXELS", 3_000_000))
        for captura in capturas:
            bruto = base64.b64decode(captura, validate=True)
            imagem = cv2.imdecode(np.frombuffer(bruto, dtype=np.uint8), cv2.IMREAD_COLOR)
            if imagem is None:
                continue
            capturas_decodificadas += 1
            altura, largura = imagem.shape[:2]
            if altura * largura > limite_pixels:
                raise DomainValidationError(f"Imagem excede o limite de {limite_pixels} pixels.")
            detector.setInputSize((largura, altura))
            _, faces = detector.detect(imagem)
            if faces is None or len(faces) == 0:
                continue
            quantidade_faces += len(faces)
            melhor_face = max(faces, key=lambda item: float(item[14]))
            alinhada = reconhecedor.alignCrop(imagem, melhor_face)
            vetor = reconhecedor.feature(alinhada)
            vetores.append(vetor.reshape(-1))

        if not vetores:
            raise DomainValidationError("Nenhum embedding facial pôde ser gerado a partir das capturas.")

        embedding = np.mean(np.vstack(vetores), axis=0).astype("float32")
        return embedding.tolist(), {
            "capturas_decodificadas": capturas_decodificadas,
            "quantidade_faces": quantidade_faces,
            "quantidade_embeddings": len(vetores),
            "modelo": "sface",
        }


def _gerar_vetor_embedding(capturas: list[str]) -> tuple[list[float], dict]:
    return GeradorEmbeddingVisao().gerar_embedding(capturas)


def calcular_similaridade_cosseno(vetor_a: list[float], vetor_b: list[float]) -> float:
    if not vetor_a or not vetor_b or len(vetor_a) != len(vetor_b):
        return 0.0

    produto = sum(float(a) * float(b) for a, b in zip(vetor_a, vetor_b, strict=True))
    norma_a = sqrt(sum(float(a) * float(a) for a in vetor_a))
    norma_b = sqrt(sum(float(b) * float(b) for b in vetor_b))
    if not norma_a or not norma_b:
        return 0.0
    return produto / (norma_a * norma_b)


def validar_rosto_unico(*, aluno: Usuario, vetor: list[float]) -> None:
    limite = float(getattr(settings, "FACE_DUPLICATE_THRESHOLD", 0.92))
    embeddings = EmbeddingFacial.objects.select_related("aluno").filter(
        ativo=True,
        status="ATIVO",
    ).exclude(aluno=aluno)

    melhor_similaridade = 0.0
    aluno_semelhante = None
    for embedding in embeddings:
        similaridade = calcular_similaridade_cosseno(vetor, embedding.vetor)
        if similaridade > melhor_similaridade:
            melhor_similaridade = similaridade
            aluno_semelhante = embedding.aluno

    if aluno_semelhante and melhor_similaridade >= limite:
        raise ConflictError(
            "Este rosto parece já estar cadastrado para outro aluno.",
            code="rosto_duplicado",
            extra={
                "similaridade": round(melhor_similaridade, 6),
                "limite": limite,
            },
        )


@transaction.atomic
def matricular_biometria_aluno(
    *,
    aluno: Usuario,
    capturas: list[str],
    versao_modelo: str,
):
    if aluno.papel != PapelUsuario.ALUNO:
        raise DomainValidationError("Matrícula biométrica só pode ser criada para alunos.")

    vetor, _ = _gerar_vetor_embedding(capturas)
    validar_rosto_unico(aluno=aluno, vetor=vetor)

    embedding, _ = EmbeddingFacial.objects.update_or_create(
        aluno=aluno,
        defaults={
            "versao_modelo": versao_modelo,
            "vetor": vetor,
            "status": "ATIVO",
            "ativo": True,
        },
    )
    return embedding
