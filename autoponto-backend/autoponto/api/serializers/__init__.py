from .academico import (
    CampusSerializer,
    CursoSerializer,
    DisciplinaSerializer,
    HorarioAulaSerializer,
    JanelaChamadaSerializer,
    MatriculaTurmaSerializer,
    PeriodoLetivoSerializer,
    PredioSerializer,
    SalaSerializer,
    TurmaSerializer,
)
from .biometria import EmbeddingFacialSerializer, MatriculaBiometricaSerializer, PerfilBiometricoSerializer
from .dispositivos import ComandoBordaSerializer, DispositivoEsp32Serializer, NoBordaSerializer, TokenNoBordaEmitirSerializer
from .frontend import MatriculaBiometricaPropriaSerializer
from .identidade import UsuarioSerializer
from .presencas import AulaSerializer, RegistroPresencaSerializer

__all__ = [
    "AulaSerializer",
    "CampusSerializer",
    "ComandoBordaSerializer",
    "CursoSerializer",
    "DisciplinaSerializer",
    "DispositivoEsp32Serializer",
    "EmbeddingFacialSerializer",
    "HorarioAulaSerializer",
    "JanelaChamadaSerializer",
    "MatriculaBiometricaSerializer",
    "MatriculaBiometricaPropriaSerializer",
    "MatriculaTurmaSerializer",
    "NoBordaSerializer",
    "PerfilBiometricoSerializer",
    "PeriodoLetivoSerializer",
    "PredioSerializer",
    "RegistroPresencaSerializer",
    "SalaSerializer",
    "TokenNoBordaEmitirSerializer",
    "TurmaSerializer",
    "UsuarioSerializer",
]
