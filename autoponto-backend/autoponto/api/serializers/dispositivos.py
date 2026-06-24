from rest_framework import serializers

from api.models import DispositivoEsp32, NoBorda


class NoBordaSerializer(serializers.ModelSerializer):
    token_prefixo_atual = serializers.SerializerMethodField()

    class Meta:
        model = NoBorda
        fields = "__all__"
        read_only_fields = (
            "id",
            "criado_em",
            "atualizado_em",
            "ultimo_sync_em",
            "token_prefixo_atual",
        )

    def get_token_prefixo_atual(self, obj):
        tokens_ativos = getattr(obj, "tokens_ativos", None)
        if tokens_ativos is not None:
            token = tokens_ativos[0] if tokens_ativos else None
            return token.prefixo_token if token else ""
        token = obj.tokens.filter(ativo=True).order_by("-criado_em").first()
        return token.prefixo_token if token else ""


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
