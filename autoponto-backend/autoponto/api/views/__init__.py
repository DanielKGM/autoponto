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
from .frontend import (
    MeView,
    MinhaBiometriaView,
    MinhasPresencasView,
    MinhasTurmasView,
    ProfessorTurmasView,
    RelatorioPresencasAlunoView,
    RelatorioPresencasTurmaDataView,
    RelatorioResumoTurmaView,
)
from .health import HealthCheckView, ReadinessCheckView
from .identidade import UsuarioViewSet
from .interscity import InterSCityActuatorWebhookView, InterSCityDiagnosticoView
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
    "InterSCityDiagnosticoView",
    "MatriculaTurmaViewSet",
    "MeView",
    "MinhaBiometriaView",
    "MinhasPresencasView",
    "MinhasTurmasView",
    "NoBordaViewSet",
    "PerfilBiometricoViewSet",
    "PeriodoLetivoViewSet",
    "PredioViewSet",
    "ProfessorTurmasView",
    "ReadinessCheckView",
    "RegistroPresencaViewSet",
    "RelatorioPresencasAlunoView",
    "RelatorioPresencasTurmaDataView",
    "RelatorioResumoTurmaView",
    "SalaViewSet",
    "TurmaViewSet",
    "UsuarioViewSet",
]
