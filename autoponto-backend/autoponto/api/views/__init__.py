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
from .autenticacao import LogoutCookieView, TokenObtainCookieView, TokenRefreshCookieView
from .biometria import EmbeddingFacialViewSet, PerfilBiometricoViewSet
from .dispositivos import ComandoBordaViewSet, DispositivoEsp32ViewSet, NoBordaViewSet
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
    "ComandoBordaViewSet",
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
    "LogoutCookieView",
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
    "TokenObtainCookieView",
    "TokenRefreshCookieView",
    "TurmaViewSet",
    "UsuarioViewSet",
]
