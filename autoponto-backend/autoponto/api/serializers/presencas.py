from rest_framework import serializers

from api.models import Aula, RegistroPresenca


class AulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aula
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class RegistroPresencaSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroPresenca
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em", "registrado_em", "registrado_por_dispositivo")

