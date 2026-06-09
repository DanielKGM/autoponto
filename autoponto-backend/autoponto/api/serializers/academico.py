from rest_framework import serializers

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
    Usuario,
)


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class PredioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Predio
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class SalaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sala
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class PeriodoLetivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoLetivo
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class DisciplinaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disciplina
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class TurmaSerializer(serializers.ModelSerializer):
    professores = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Usuario.objects.filter(papel=PapelUsuario.PROFESSOR),
    )

    class Meta:
        model = Turma
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class MatriculaTurmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatriculaTurma
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class HorarioAulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioAula
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class JanelaChamadaSerializer(serializers.Serializer):
    abre_chamada_minutos = serializers.IntegerField(min_value=0)
    fecha_chamada_minutos = serializers.IntegerField(min_value=1, required=False, allow_null=True)
