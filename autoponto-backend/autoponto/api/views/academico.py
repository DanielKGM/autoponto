from api.models import (
    Campus,
    Curso,
    Disciplina,
    HorarioPadraoUFMA,
    MatriculaTurma,
    PapelUsuario,
    PeriodoLetivo,
    Predio,
    Sala,
    Turma,
)
from api.serializers.academico import (
    CampusSerializer,
    CursoSerializer,
    DisciplinaSerializer,
    HorarioPadraoUFMASerializer,
    MatriculaTurmaSerializer,
    PeriodoLetivoSerializer,
    PredioSerializer,
    SalaSerializer,
    TurmaSerializer,
)
from api.services.aulas import sincronizar_aulas_da_turma
from .mixins import AdminReadableModelViewSet


class CampusViewSet(AdminReadableModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer
    filterset_fields = ("ativo",)
    search_fields = ("nome",)


class PredioViewSet(AdminReadableModelViewSet):
    queryset = Predio.objects.select_related("campus").all()
    serializer_class = PredioSerializer
    filterset_fields = ("campus", "ativo")
    search_fields = ("nome",)


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
    search_fields = ("nome",)


class DisciplinaViewSet(AdminReadableModelViewSet):
    queryset = Disciplina.objects.select_related("curso").all()
    serializer_class = DisciplinaSerializer
    filterset_fields = ("curso", "ativo")
    search_fields = ("nome", "codigo", "curso__nome")


class TurmaViewSet(AdminReadableModelViewSet):
    queryset = Turma.objects.select_related("periodo_letivo", "disciplina").prefetch_related("professores").all()
    serializer_class = TurmaSerializer
    filterset_fields = ("periodo_letivo", "disciplina", "professores", "ativo")
    search_fields = ("codigo", "disciplina__nome", "disciplina__codigo")

    def filtrar_queryset_por_usuario(self, queryset, usuario):
        if getattr(usuario, "papel", None) == PapelUsuario.PROFESSOR:
            return queryset.filter(professores=usuario).distinct()
        if getattr(usuario, "papel", None) == PapelUsuario.ALUNO:
            return queryset.filter(matriculas__aluno=usuario, matriculas__ativo=True).distinct()
        return queryset.none()

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save(update_fields=["ativo", "atualizado_em"])
        sincronizar_aulas_da_turma(instance, [])


class MatriculaTurmaViewSet(AdminReadableModelViewSet):
    queryset = MatriculaTurma.objects.select_related("turma", "aluno").all()
    serializer_class = MatriculaTurmaSerializer
    filterset_fields = ("turma", "aluno", "ativo")

    def filtrar_queryset_por_usuario(self, queryset, usuario):
        if getattr(usuario, "papel", None) == PapelUsuario.PROFESSOR:
            return queryset.filter(turma__professores=usuario).distinct()
        if getattr(usuario, "papel", None) == PapelUsuario.ALUNO:
            return queryset.filter(aluno=usuario)
        return queryset.none()


class HorarioPadraoUFMAViewSet(AdminReadableModelViewSet):
    queryset = HorarioPadraoUFMA.objects.all()
    serializer_class = HorarioPadraoUFMASerializer
    filterset_fields = ("dia_semana", "ativo")
    search_fields = ("codigo",)

    def filtrar_queryset_por_usuario(self, queryset, usuario):
        return queryset.filter(ativo=True)
