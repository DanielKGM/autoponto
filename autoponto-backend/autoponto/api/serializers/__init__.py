from .academico import (
    CampusSerializer,
    CursoSerializer,
    DisciplinaSerializer,
    HorarioAulaSerializer,
    MatriculaTurmaSerializer,
    PeriodoLetivoSerializer,
    PredioSerializer,
    SalaSerializer,
    TurmaSerializer,
)
from .biometria import EmbeddingFacialSerializer, MatriculaBiometricaSerializer, PerfilBiometricoSerializer
from .dispositivos import ComandoBordaSerializer, DispositivoEsp32Serializer, NoBordaSerializer, TokenNoBordaEmitirSerializer
from .frontend import MatriculaBiometricaPropriaSerializer, RelatorioPeriodoSerializer
from .identidade import UsuarioSerializer
from .presencas import (
    AulaSerializer,
    EventoReconhecimentoSerializer,
    EventoReconhecimentoSubmissionSerializer,
    RegistroPresencaSerializer,
)

__all__ = [
    "AulaSerializer",
    "CampusSerializer",
    "ComandoBordaSerializer",
    "CursoSerializer",
    "DisciplinaSerializer",
    "DispositivoEsp32Serializer",
    "EmbeddingFacialSerializer",
    "EventoReconhecimentoSerializer",
    "EventoReconhecimentoSubmissionSerializer",
    "HorarioAulaSerializer",
    "MatriculaBiometricaSerializer",
    "MatriculaBiometricaPropriaSerializer",
    "MatriculaTurmaSerializer",
    "NoBordaSerializer",
    "PerfilBiometricoSerializer",
    "PeriodoLetivoSerializer",
    "PredioSerializer",
    "RelatorioPeriodoSerializer",
    "RegistroPresencaSerializer",
    "SalaSerializer",
    "TokenNoBordaEmitirSerializer",
    "TurmaSerializer",
    "UsuarioSerializer",
]
