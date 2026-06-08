from .academico import (
    CampusViewSet,
    CursoViewSet,
    DisciplinaViewSet,
    HorarioAulaViewSet,
    MatriculaTurmaViewSet,
    PeriodoLetivoViewSet,
    PredioViewSet,
    SalaViewSet,
    TurmaViewSet,
)
from .biometria import EmbeddingFacialViewSet, PerfilBiometricoViewSet
from .dispositivos import DispositivoEsp32ViewSet, NoBordaViewSet
from .edge_contract import (
    EdgeAttendanceSlashAliasView,
    EdgeAttendanceView,
    EdgeCommandAckSlashAliasView,
    EdgeCommandAckView,
    EdgeCommandListSlashAliasView,
    EdgeCommandListView,
    EdgePullSlashAliasView,
    EdgePullView,
)
from .health import HealthCheckView, ReadinessCheckView
from .identidade import UsuarioViewSet
from .interscity import InterSCityActuatorWebhookView
from .presencas import AulaViewSet, RegistroPresencaViewSet

__all__ = [
    "AulaViewSet",
    "CampusViewSet",
    "CursoViewSet",
    "DisciplinaViewSet",
    "DispositivoEsp32ViewSet",
    "EdgeAttendanceSlashAliasView",
    "EdgeAttendanceView",
    "EdgeCommandAckSlashAliasView",
    "EdgeCommandAckView",
    "EdgeCommandListSlashAliasView",
    "EdgeCommandListView",
    "EdgePullSlashAliasView",
    "EdgePullView",
    "EmbeddingFacialViewSet",
    "HealthCheckView",
    "HorarioAulaViewSet",
    "InterSCityActuatorWebhookView",
    "MatriculaTurmaViewSet",
    "NoBordaViewSet",
    "PerfilBiometricoViewSet",
    "PeriodoLetivoViewSet",
    "PredioViewSet",
    "ReadinessCheckView",
    "RegistroPresencaViewSet",
    "SalaViewSet",
    "TurmaViewSet",
    "UsuarioViewSet",
]
