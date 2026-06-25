from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views.academico import (
    CampusViewSet,
    CursoViewSet,
    DisciplinaViewSet,
    HorarioPadraoUFMAViewSet,
    MatriculaTurmaViewSet,
    PeriodoLetivoViewSet,
    PredioViewSet,
    SalaViewSet,
    TurmaViewSet,
)
from api.views.autenticacao import (
    LogoutCookieView,
    TokenObtainCookieView,
    TokenRefreshCookieView,
)
from api.views.biometria import EmbeddingFacialViewSet
from api.views.dispositivos import DispositivoEsp32ViewSet, NoBordaViewSet
from api.views.edge_contract import EdgeAttendanceView, EdgePullView
from api.views.frontend import (
    DashboardAlunoView,
    DashboardProfessorView,
    MeView,
    MinhaBiometriaView,
    MinhaFrequenciaView,
    MeuCalendarioAulasView,
    MinhasPresencasView,
    MinhasTurmasView,
    ProfessorTurmaFrequenciaView,
    ProfessorTurmasView,
    RelatorioPresencasAlunoView,
    RelatorioPresencasTurmaDataView,
    RelatorioResumoTurmaView,
    TurmaAulaDetalheView,
)
from api.views.health import HealthCheckView, ReadinessCheckView
from api.views.identidade import UsuarioViewSet
from api.views.interscity import InterSCityDiagnosticoView
from api.views.mapa_publico import (
    MapaDispositivoHistoricoView,
    MapaDispositivosPublicosView,
    MapaNosPublicosView,
)
from api.views.presencas import AulaViewSet, RegistroPresencaViewSet

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")
router.register("campi", CampusViewSet, basename="campus")
router.register("predios", PredioViewSet, basename="predio")
router.register("salas", SalaViewSet, basename="sala")
router.register("periodos-letivos", PeriodoLetivoViewSet, basename="periodo-letivo")
router.register("cursos", CursoViewSet, basename="curso")
router.register("disciplinas", DisciplinaViewSet, basename="disciplina")
router.register("turmas", TurmaViewSet, basename="turma")
router.register("matriculas-turma", MatriculaTurmaViewSet, basename="matricula-turma")
router.register(
    "horarios-padrao-ufma", HorarioPadraoUFMAViewSet, basename="horario-padrao-ufma"
)
router.register("nos-borda", NoBordaViewSet, basename="no-borda")
router.register(
    "dispositivos-esp32", DispositivoEsp32ViewSet, basename="dispositivo-esp32"
)
router.register("aulas", AulaViewSet, basename="aula")
router.register("presencas", RegistroPresencaViewSet, basename="presenca")
router.register(
    "embeddings-faciais", EmbeddingFacialViewSet, basename="embedding-facial"
)

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("ready/", ReadinessCheckView.as_view(), name="ready"),
    path("auth/token/", TokenObtainCookieView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshCookieView.as_view(), name="token_refresh"),
    path("auth/logout/", LogoutCookieView.as_view(), name="token_logout"),
    path("me/", MeView.as_view(), name="me"),
    path("me/turmas/", MinhasTurmasView.as_view(), name="me-turmas"),
    path("me/presencas/", MinhasPresencasView.as_view(), name="me-presencas"),
    path("me/calendario-aulas/", MeuCalendarioAulasView.as_view(), name="me-calendario-aulas"),
    path("me/dashboard-aluno/", DashboardAlunoView.as_view(), name="me-dashboard-aluno"),
    path("me/frequencia/", MinhaFrequenciaView.as_view(), name="me-frequencia"),
    path("me/biometria/", MinhaBiometriaView.as_view(), name="me-biometria"),
    path("professor/dashboard/", DashboardProfessorView.as_view(), name="professor-dashboard"),
    path("professor/turmas/", ProfessorTurmasView.as_view(), name="professor-turmas"),
    path(
        "professor/turmas/<uuid:turma_id>/frequencia/",
        ProfessorTurmaFrequenciaView.as_view(),
        name="professor-turma-frequencia",
    ),
    path("turmas/<uuid:turma_id>/aula/", TurmaAulaDetalheView.as_view(), name="turma-aula-geral"),
    path(
        "turmas/<uuid:turma_id>/aula/<uuid:aula_id>/",
        TurmaAulaDetalheView.as_view(),
        name="turma-aula-detalhe",
    ),
    path(
        "relatorios/turmas/<uuid:turma_id>/presencas/",
        RelatorioPresencasTurmaDataView.as_view(),
        name="relatorio-turma-presencas-data",
    ),
    path(
        "relatorios/turmas/<uuid:turma_id>/resumo/",
        RelatorioResumoTurmaView.as_view(),
        name="relatorio-turma-resumo",
    ),
    path(
        "relatorios/alunos/<uuid:aluno_id>/presencas/",
        RelatorioPresencasAlunoView.as_view(),
        name="relatorio-aluno-presencas",
    ),
    path("edge/pull/", EdgePullView.as_view(), name="edge-pull"),
    path("edge/attendance/", EdgeAttendanceView.as_view(), name="edge-attendance"),
    path(
        "public/mapa/nos/",
        MapaNosPublicosView.as_view(),
        name="mapa-nos-publicos",
    ),
    path(
        "public/mapa/dispositivos/",
        MapaDispositivosPublicosView.as_view(),
        name="mapa-dispositivos-publicos",
    ),
    path(
        "public/mapa/dispositivos/<uuid:dispositivo_id>/historico/",
        MapaDispositivoHistoricoView.as_view(),
        name="mapa-dispositivo-historico",
    ),
    path(
        "interscity/diagnostico/",
        InterSCityDiagnosticoView.as_view(),
        name="interscity-diagnostico",
    ),
    path("", include(router.urls)),
]
