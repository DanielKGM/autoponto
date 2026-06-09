import base64
from math import sqrt

from django.conf import settings
from django.db import transaction

from api.models import EmbeddingFacial, PapelUsuario, PerfilBiometrico, Usuario
from .errors import ConflictError, DomainValidationError


class GeradorEmbeddingVisao:
    def __init__(self, caminho_modelo_deteccao: str | None = None, caminho_modelo_reconhecimento: str | None = None):
        self.caminho_modelo_deteccao = caminho_modelo_deteccao or getattr(settings, "FACE_DETECT_MODEL_PATH", "")
        self.caminho_modelo_reconhecimento = caminho_modelo_reconhecimento or getattr(settings, "FACE_RECOG_MODEL_PATH", "")

    def gerar_embedding(self, capturas: list[str]) -> tuple[list[float], dict]:
        if not capturas:
            raise DomainValidationError("Ao menos uma captura é necessária para gerar o embedding.")

        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            raise DomainValidationError("OpenCV e NumPy são necessários para gerar embeddings faciais.") from exc

        detector = cv2.FaceDetectorYN.create(
            self.caminho_modelo_deteccao,
            "",
            (240, 240),
            float(getattr(settings, "FACE_SCORE_THRESHOLD", 0.85)),
            0.3,
            5000,
        )
        reconhecedor = cv2.FaceRecognizerSF.create(self.caminho_modelo_reconhecimento, "")
        vetores = []
        capturas_decodificadas = 0
        quantidade_faces = 0

        for captura in capturas:
            bruto = base64.b64decode(captura)
            imagem = cv2.imdecode(np.frombuffer(bruto, dtype=np.uint8), cv2.IMREAD_COLOR)
            if imagem is None:
                continue
            capturas_decodificadas += 1
            altura, largura = imagem.shape[:2]
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
    embeddings = EmbeddingFacial.objects.select_related("perfil", "perfil__aluno").filter(
        ativo=True,
        status="ATIVO",
    ).exclude(perfil__aluno=aluno)

    melhor_similaridade = 0.0
    aluno_semelhante = None
    for embedding in embeddings:
        similaridade = calcular_similaridade_cosseno(vetor, embedding.vetor)
        if similaridade > melhor_similaridade:
            melhor_similaridade = similaridade
            aluno_semelhante = embedding.perfil.aluno

    if aluno_semelhante and melhor_similaridade >= limite:
        raise ConflictError(
            "Este rosto parece ja estar cadastrado para outro aluno.",
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

    perfil, _ = PerfilBiometrico.objects.get_or_create(aluno=aluno, defaults={"status": "PENDENTE"})
    perfil.status = "ATIVO"
    perfil.save()

    perfil.embeddings.filter(ativo=True).update(ativo=False, status="INATIVO")
    embedding = EmbeddingFacial.objects.create(
        perfil=perfil,
        versao_modelo=versao_modelo,
        vetor=vetor,
        status="ATIVO",
        ativo=True,
    )
    return perfil, embedding
