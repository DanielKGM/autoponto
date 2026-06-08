import base64
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from api.models import EmbeddingFacial, PapelUsuario, PerfilBiometrico, Usuario
from .errors import DomainValidationError


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
            melhor_face = sorted(faces, key=lambda item: float(item[14]), reverse=True)[0]
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


@transaction.atomic
def matricular_biometria_aluno(
    *,
    aluno: Usuario,
    capturas: list[str],
    versao_modelo: str,
    pontuacao_qualidade: float = 0.95,
    metadados_origem: dict | None = None,
):
    if aluno.papel != PapelUsuario.ALUNO:
        raise DomainValidationError("Matrícula biométrica só pode ser criada para alunos.")

    perfil, _ = PerfilBiometrico.objects.get_or_create(aluno=aluno, defaults={"status": "PENDENTE"})
    perfil.status = "ATIVO"
    perfil.save()

    vetor, metadados_gerados = _gerar_vetor_embedding(capturas)
    metadados = {**(metadados_origem or {}), **metadados_gerados}
    metadados.pop("capturas", None)
    metadados.pop("frames", None)

    perfil.embeddings.filter(ativo=True).update(ativo=False, status="INATIVO")
    embedding = EmbeddingFacial.objects.create(
        perfil=perfil,
        versao_modelo=versao_modelo,
        vetor=vetor,
        pontuacao_qualidade=Decimal(str(pontuacao_qualidade)).quantize(Decimal("0.0001")),
        metadados_origem=metadados,
        status="ATIVO",
        ativo=True,
    )
    return perfil, embedding
