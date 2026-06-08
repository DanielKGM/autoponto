from rest_framework import serializers


class MatriculaBiometricaPropriaSerializer(serializers.Serializer):
    capturas = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    versao_modelo = serializers.CharField(max_length=50, required=False, default="sface")
    pontuacao_qualidade = serializers.FloatField(required=False, default=0.95)
    metadados_origem = serializers.JSONField(required=False, default=dict)


class RelatorioPeriodoSerializer(serializers.Serializer):
    inicio = serializers.DateField(required=False)
    fim = serializers.DateField(required=False)
