from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.views import (
    AulaViewSet,
    CampusViewSet,
    CursoViewSet,
    DisciplinaViewSet,
    DispositivoEsp32ViewSet,
    EdgeAttendanceSlashAliasView,
    EdgeAttendanceView,
    EdgeCommandAckSlashAliasView,
    EdgeCommandAckView,
    EdgeCommandListSlashAliasView,
    EdgeCommandListView,
    EdgePullSlashAliasView,
    EdgePullView,
    EmbeddingFacialViewSet,
    HealthCheckView,
    HorarioAulaViewSet,
    InterSCityActuatorWebhookView,
    MatriculaTurmaViewSet,
    NoBordaViewSet,
    PerfilBiometricoViewSet,
    PeriodoLetivoViewSet,
    PredioViewSet,
    ReadinessCheckView,
    RegistroPresencaViewSet,
    SalaViewSet,
    TurmaViewSet,
    UsuarioViewSet,
)

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
router.register("horarios-aula", HorarioAulaViewSet, basename="horario-aula")
router.register("nos-borda", NoBordaViewSet, basename="no-borda")
router.register("dispositivos-esp32", DispositivoEsp32ViewSet, basename="dispositivo-esp32")
router.register("aulas", AulaViewSet, basename="aula")
router.register("presencas", RegistroPresencaViewSet, basename="presenca")
router.register("perfis-biometricos", PerfilBiometricoViewSet, basename="perfil-biometrico")
router.register("embeddings-faciais", EmbeddingFacialViewSet, basename="embedding-facial")

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("ready/", ReadinessCheckView.as_view(), name="ready"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("edge/pull", EdgePullView.as_view(), name="edge-pull-noslash"),
    path("edge/pull/", EdgePullSlashAliasView.as_view(), name="edge-pull"),
    path("edge/attendance", EdgeAttendanceView.as_view(), name="edge-attendance-noslash"),
    path("edge/attendance/", EdgeAttendanceSlashAliasView.as_view(), name="edge-attendance"),
    path("edge/commands", EdgeCommandListView.as_view(), name="edge-commands-noslash"),
    path("edge/commands/", EdgeCommandListSlashAliasView.as_view(), name="edge-commands"),
    path("edge/commands/ack", EdgeCommandAckView.as_view(), name="edge-commands-ack-noslash"),
    path("edge/commands/ack/", EdgeCommandAckSlashAliasView.as_view(), name="edge-commands-ack"),
    path("interscity/webhooks/actuator/", InterSCityActuatorWebhookView.as_view(), name="interscity-actuator-webhook"),
    path("", include(router.urls)),
]
