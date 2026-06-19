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
from .interscity import InterSCityDiagnosticoView
from .mapa_publico import MapaDispositivoHistoricoView, MapaDispositivosPublicosView
from .presencas import AulaViewSet, RegistroPresencaViewSet

__all__ = [
    "AulaViewSet",
    "CampusViewSet",
    "CursoViewSet",
    "DisciplinaViewSet",
    "DispositivoEsp32ViewSet",
    "EdgeAttendanceSlashAliasView",
    "EdgeAttendanceView",
    "EdgePullSlashAliasView",
    "EdgePullView",
    "EmbeddingFacialViewSet",
    "HealthCheckView",
    "HorarioAulaViewSet",
    "HorarioPadraoUFMAViewSet",
    "InterSCityDiagnosticoView",
    "LogoutCookieView",
    "MatriculaTurmaViewSet",
    "MapaDispositivoHistoricoView",
    "MapaDispositivosPublicosView",
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
