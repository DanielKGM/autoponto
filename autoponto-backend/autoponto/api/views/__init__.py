from .academico import (
    CampusViewSet,
    CursoViewSet,
    DisciplinaViewSet,
    HorarioAulaViewSet,
    HorarioPadraoUFMAViewSet,
    MatriculaTurmaViewSet,
    PeriodoLetivoViewSet,
    PredioViewSet,
    SalaViewSet,
    TurmaViewSet,
)
from .autenticacao import LogoutCookieView, TokenObtainCookieView, TokenRefreshCookieView
from .biometria import EmbeddingFacialViewSet, PerfilBiometricoViewSet
from .dispositivos import DispositivoEsp32ViewSet, NoBordaViewSet
from .edge_contract import (
    EdgeAttendanceSlashAliasView,
    EdgeAttendanceView,
    EdgeDeviceStatusSlashAliasView,
    EdgeDeviceStatusView,
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
from .interscity import InterSCityDiagnosticoView, InterSCitySincronizarRecursosView
from .presencas import AulaViewSet, RegistroPresencaViewSet

__all__ = [
    "AulaViewSet",
    "CampusViewSet",
    "CursoViewSet",
    "DisciplinaViewSet",
    "DispositivoEsp32ViewSet",
    "EdgeAttendanceSlashAliasView",
    "EdgeAttendanceView",
    "EdgeDeviceStatusSlashAliasView",
    "EdgeDeviceStatusView",
    "EdgePullSlashAliasView",
    "EdgePullView",
    "EmbeddingFacialViewSet",
    "HealthCheckView",
    "HorarioAulaViewSet",
    "HorarioPadraoUFMAViewSet",
    "InterSCityDiagnosticoView",
    "InterSCitySincronizarRecursosView",
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
