from rest_framework import serializers

from api.models import DispositivoEsp32, NoBorda


class NoBordaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoBorda
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em", "ultimo_sync_em")


class DispositivoEsp32Serializer(serializers.ModelSerializer):
    sala_nome = serializers.CharField(source="sala.nome", read_only=True)
    no_codigo = serializers.CharField(source="no.codigo", read_only=True)

    class Meta:
        model = DispositivoEsp32
        fields = "__all__"
        read_only_fields = (
            "id",
            "criado_em",
            "atualizado_em",
            "sala_nome",
            "no_codigo",
        )


class TokenNoBordaEmitirSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=100, default="default")
    expira_em = serializers.DateTimeField(required=False, allow_null=True)
