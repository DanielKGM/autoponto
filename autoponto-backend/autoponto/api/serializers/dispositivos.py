from rest_framework import serializers

from api.models import ComandoBorda, DispositivoEsp32, NoBorda


class NoBordaSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoBorda
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em", "ultimo_sync_em")


class DispositivoEsp32Serializer(serializers.ModelSerializer):
    class Meta:
        model = DispositivoEsp32
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em", "ultimo_sync_em")


class TokenNoBordaEmitirSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=100, default="default")
    expira_em = serializers.DateTimeField(required=False, allow_null=True)


class ComandoBordaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComandoBorda
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em", "origem", "criado_por", "entregue_em")
        extra_kwargs = {"id_origem": {"required": False, "allow_blank": True}}
        validators = []
