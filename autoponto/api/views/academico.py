from api.models import Campus, Curso, Disciplina, HorarioAula, MatriculaTurma, PeriodoLetivo, Predio, Sala, Turma
from api.serializers import (
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
    search_fields = ("nome", "codigo", "turno")


class DisciplinaViewSet(AdminReadableModelViewSet):
    queryset = Disciplina.objects.select_related("curso").all()
    serializer_class = DisciplinaSerializer
    filterset_fields = ("curso", "ativo", "obrigatoria", "periodo_sugerido")
    search_fields = ("nome", "codigo", "curso__nome", "curso__codigo")


class TurmaViewSet(AdminReadableModelViewSet):
    queryset = Turma.objects.select_related("periodo_letivo", "disciplina").prefetch_related("professores").all()
    serializer_class = TurmaSerializer
    filterset_fields = ("periodo_letivo", "disciplina", "professores", "ativo")
    search_fields = ("codigo", "nome", "disciplina__nome", "disciplina__codigo")


class MatriculaTurmaViewSet(AdminReadableModelViewSet):
    queryset = MatriculaTurma.objects.select_related("turma", "aluno").all()
    serializer_class = MatriculaTurmaSerializer
    filterset_fields = ("turma", "aluno", "ativo")


class HorarioAulaViewSet(AdminReadableModelViewSet):
    queryset = HorarioAula.objects.select_related("turma", "turma__disciplina", "sala").all()
    serializer_class = HorarioAulaSerializer
    filterset_fields = ("turma", "sala", "dia_semana", "ativo")
