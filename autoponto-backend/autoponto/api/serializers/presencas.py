from rest_framework import serializers

from api.models import Aula, EventoReconhecimento, PapelUsuario, RegistroPresenca, Usuario


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


class EventoReconhecimentoSubmissionSerializer(serializers.Serializer):
    aula = serializers.PrimaryKeyRelatedField(queryset=Aula.objects.all())
    aluno_candidato = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(papel=PapelUsuario.ALUNO),
        required=False,
        allow_null=True,
    )
    confianca = serializers.DecimalField(max_digits=5, decimal_places=4)
    reconhecido = serializers.BooleanField()


class EventoReconhecimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventoReconhecimento
        fields = "__all__"
        read_only_fields = ("id", "criado_em", "atualizado_em")
