from rest_framework import serializers

from api.services.biometria import validar_capturas_biometricas
from api.services.errors import DomainValidationError


class MatriculaBiometricaPropriaSerializer(serializers.Serializer):
    capturas = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    versao_modelo = serializers.CharField(max_length=50, required=False, default="sface")

    def validate_capturas(self, value):
        try:
            return validar_capturas_biometricas(value)
        except DomainValidationError as erro:
            raise serializers.ValidationError(erro.message) from erro
