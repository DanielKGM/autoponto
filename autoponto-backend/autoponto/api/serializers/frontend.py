from rest_framework import serializers


class MatriculaBiometricaPropriaSerializer(serializers.Serializer):
    capturas = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    versao_modelo = serializers.CharField(max_length=50, required=False, default="sface")
