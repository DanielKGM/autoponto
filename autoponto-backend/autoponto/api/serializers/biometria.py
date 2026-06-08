from rest_framework import serializers

from api.models import EmbeddingFacial, PerfilBiometrico


class PerfilBiometricoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilBiometrico
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")


class EmbeddingFacialSerializer(serializers.ModelSerializer):
    aluno_id = serializers.UUIDField(source="perfil.aluno_id", read_only=True)

    class Meta:
        model = EmbeddingFacial
        fields = (
            "id",
            "aluno_id",
            "perfil",
            "versao_modelo",
            "vetor",
            "pontuacao_qualidade",
            "metadados_origem",
            "status",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("id", "criado_em", "atualizado_em")


class MatriculaBiometricaSerializer(serializers.Serializer):
    aluno_id = serializers.UUIDField()
    capturas = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    versao_modelo = serializers.CharField(max_length=50)
    pontuacao_qualidade = serializers.FloatField(required=False, default=0.95)
    metadados_origem = serializers.JSONField(required=False)
