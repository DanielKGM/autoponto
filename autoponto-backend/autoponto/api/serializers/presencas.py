from rest_framework import serializers

from api.models import Aula, RegistroPresenca
from api.selectors.aulas import status_aula


class AulaSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Aula
        fields = (
            "id",
            "criado_em",
            "atualizado_em",
            "turma",
            "sala",
            "horario_padrao",
            "data",
            "inicio",
            "fim",
            "cancelada_em",
            "cancelada_por",
            "fechada_em",
            "fechada_por",
            "status",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em", "status")

    def get_status(self, obj):
        return status_aula(obj)


class RegistroPresencaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroPresenca
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em", "registrado_em", "registrado_por_dispositivo")
