from .academico import (
    CampusSerializer,
    CursoSerializer,
    DisciplinaSerializer,
    HorarioAulaSerializer,
    HorarioPadraoUFMASerializer,
    MatriculaTurmaSerializer,
    PeriodoLetivoSerializer,
    PredioSerializer,
    SalaSerializer,
    TurmaSerializer,
)
from .biometria import EmbeddingFacialSerializer, MatriculaBiometricaSerializer, PerfilBiometricoSerializer
from .dispositivos import DispositivoEsp32Serializer, NoBordaSerializer, TokenNoBordaEmitirSerializer
from .frontend import MatriculaBiometricaPropriaSerializer
from .identidade import UsuarioSerializer
from .presencas import AulaSerializer, RegistroPresencaSerializer

__all__ = [
    "AulaSerializer",
    "CampusSerializer",
    "CursoSerializer",
    "DisciplinaSerializer",
    "DispositivoEsp32Serializer",
    "EmbeddingFacialSerializer",
    "HorarioAulaSerializer",
    "HorarioPadraoUFMASerializer",
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
