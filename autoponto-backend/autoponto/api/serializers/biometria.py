from rest_framework import serializers

from api.models import EmbeddingFacial
from api.services.biometria import validar_capturas_biometricas
from api.services.errors import DomainValidationError


class EmbeddingFacialSerializer(serializers.ModelSerializer):
    aluno_id = serializers.UUIDField(source="aluno.id", read_only=True)
    aluno_nome = serializers.CharField(source="aluno.nome_completo", read_only=True)

    class Meta:
        model = EmbeddingFacial
        fields = (
            "id",
            "aluno",
            "aluno_id",
            "aluno_nome",
            "versao_modelo",
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

    def validate_capturas(self, value):
        try:
            return validar_capturas_biometricas(value)
        except DomainValidationError as erro:
            raise serializers.ValidationError(erro.message) from erro
