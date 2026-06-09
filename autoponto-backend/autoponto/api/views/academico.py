from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.models import (
    Campus,
    Curso,
    Disciplina,
    HorarioAula,
    MatriculaTurma,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    Sala,
    Turma,
)
from api.permissions import IsProfessorOuAdministrador
from api.serializers import (
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
from api.services import recalcular_janelas_aulas_futuras
from .mixins import AdminReadableModelViewSet


class CampusViewSet(AdminReadableModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    filterset_fields = ("ativo",)
    search_fields = ("nome", "codigo")


class PredioViewSet(AdminReadableModelViewSet):
    queryset = Predio.objects.select_related("campus").all()
    serializer_class = PredioSerializer
    filterset_fields = ("campus", "ativo")
    search_fields = ("nome", "codigo")


class SalaViewSet(AdminReadableModelViewSet):
    queryset = Sala.objects.select_related("predio", "predio__campus").all()
    serializer_class = SalaSerializer
    filterset_fields = ("predio", "ativo")
    search_fields = ("nome", "codigo")


class PeriodoLetivoViewSet(AdminReadableModelViewSet):
    queryset = PeriodoLetivo.objects.all()
    serializer_class = PeriodoLetivoSerializer
    filterset_fields = ("ativo",)
    search_fields = ("nome",)


class CursoViewSet(AdminReadableModelViewSet):
    queryset = Curso.objects.select_related("campus").all()
    serializer_class = CursoSerializer
    filterset_fields = ("campus", "ativo")
    search_fields = ("nome", "codigo")


class DisciplinaViewSet(AdminReadableModelViewSet):
    queryset = Disciplina.objects.select_related("curso").all()
    serializer_class = DisciplinaSerializer
    filterset_fields = ("curso", "ativo")
    search_fields = ("nome", "codigo", "curso__nome", "curso__codigo")


class TurmaViewSet(AdminReadableModelViewSet):
    queryset = Turma.objects.select_related("periodo_letivo", "disciplina").prefetch_related("professores").all()
    serializer_class = TurmaSerializer
    filterset_fields = ("periodo_letivo", "disciplina", "professores", "ativo")
    search_fields = ("codigo", "disciplina__nome", "disciplina__codigo")


class MatriculaTurmaViewSet(AdminReadableModelViewSet):
    queryset = MatriculaTurma.objects.select_related("turma", "aluno").all()
    serializer_class = MatriculaTurmaSerializer
    filterset_fields = ("turma", "aluno", "ativo")


class HorarioAulaViewSet(AdminReadableModelViewSet):
    queryset = HorarioAula.objects.select_related("turma", "turma__disciplina", "sala").all()
    serializer_class = HorarioAulaSerializer
    filterset_fields = ("turma", "sala", "dia_semana", "ativo")

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsProfessorOuAdministrador],
        serializer_class=JanelaChamadaSerializer,
        url_path="definir-janela-chamada",
    )
    def definir_janela_chamada(self, request, pk=None):
        horario = self.get_object()
        if request.user.papel != PapelUsuario.ADMINISTRADOR:
            if not horario.turma.professores.filter(id=request.user.id).exists():
                raise PermissionDenied("Você não pode alterar a janela de chamada desta turma.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        horario.abre_chamada_minutos = serializer.validated_data["abre_chamada_minutos"]
        horario.fecha_chamada_minutos = serializer.validated_data.get("fecha_chamada_minutos")
        horario.save(update_fields=["abre_chamada_minutos", "fecha_chamada_minutos", "atualizado_em"])
        aulas_atualizadas = recalcular_janelas_aulas_futuras(horario)
        return Response(
            {
                "horario": HorarioAulaSerializer(horario, context=self.get_serializer_context()).data,
                "aulas_atualizadas": aulas_atualizadas,
            }
        )
