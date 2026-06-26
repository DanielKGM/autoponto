from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from api.models import (
    Aula,
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
    Usuario,
)
from api.services.aulas import sincronizar_aulas_da_turma
from api.services.errors import DomainValidationError


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
    horarios = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = Turma
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")

    def validate_horarios(self, value):
        horarios = []
        erros = []
        for indice, item in enumerate(value, start=1):
            sala_id = item.get("sala")
            horario_padrao_id = item.get("horario_padrao")
            if not sala_id or not horario_padrao_id:
                erros.append(f"Horario {indice}: informe sala e horario_padrao.")
                continue
            try:
                sala = Sala.objects.get(pk=sala_id)
                horario_padrao = HorarioPadraoUFMA.objects.get(pk=horario_padrao_id, ativo=True)
            except Sala.DoesNotExist:
                erros.append(f"Horario {indice}: sala inexistente.")
                continue
            except HorarioPadraoUFMA.DoesNotExist:
                erros.append(f"Horario {indice}: horario_padrao inexistente ou inativo.")
                continue
            horarios.append({"sala": sala, "horario_padrao": horario_padrao})
        if erros:
            raise serializers.ValidationError(erros)
        return horarios

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["horarios"] = self.horarios_futuros_da_turma(instance)
        return data

    def horarios_futuros_da_turma(self, turma):
        aulas = (
            Aula.objects.select_related("sala", "horario_padrao")
            .filter(turma=turma, data__gte=timezone.localdate())
            .exclude(status=Aula.STATUS_CANCELADA)
            .order_by("horario_padrao__dia_semana", "horario_padrao__horario_inicio", "sala__codigo", "id")
        )
        vistos = set()
        horarios = []
        for aula in aulas:
            par = (aula.sala_id, aula.horario_padrao_id)
            if par in vistos:
                continue
            vistos.add(par)
            horarios.append({"sala": str(aula.sala_id), "horario_padrao": str(aula.horario_padrao_id)})
        return horarios

    def validate(self, attrs):
        horarios_informados = self.initial_data.get("horarios") is not None
        ativo = attrs.get("ativo", self.instance.ativo if self.instance else True)
        if not self.instance and ativo and not horarios_informados:
            raise serializers.ValidationError({"horarios": "Informe ao menos um horario para criar uma turma ativa."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        horarios = validated_data.pop("horarios", [])
        turma = super().create(validated_data)
        try:
            sincronizar_aulas_da_turma(turma, horarios)
        except DomainValidationError as erro:
            raise serializers.ValidationError(erro.message) from erro
        return turma

    @transaction.atomic
    def update(self, instance, validated_data):
        horarios = validated_data.pop("horarios", None)
        turma = super().update(instance, validated_data)
        if horarios is not None or not turma.ativo:
            try:
                sincronizar_aulas_da_turma(turma, horarios or [])
            except DomainValidationError as erro:
                raise serializers.ValidationError(erro.message) from erro
        return turma


class MatriculaTurmaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatriculaTurma
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class HorarioPadraoUFMASerializer(serializers.ModelSerializer):
    class Meta:
        model = HorarioPadraoUFMA
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")
