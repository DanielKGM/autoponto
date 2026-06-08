from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import EmbeddingFacial, PerfilBiometrico, Usuario
from api.permissions import IsAdministrador, IsProfessorOuAdministrador
from api.serializers import EmbeddingFacialSerializer, MatriculaBiometricaSerializer, PerfilBiometricoSerializer
from api.services import matricular_biometria_aluno
from .mixins import AdminReadableModelViewSet


class PerfilBiometricoViewSet(AdminReadableModelViewSet):
    queryset = PerfilBiometrico.objects.select_related("aluno").all()
    serializer_class = PerfilBiometricoSerializer
    filterset_fields = ("status", "aluno")

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAdministrador],
        serializer_class=MatriculaBiometricaSerializer,
        url_path="matricular",
    )
    def matricular(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        aluno = get_object_or_404(Usuario, pk=serializer.validated_data["aluno_id"])
        perfil, embedding = matricular_biometria_aluno(
            aluno=aluno,
            capturas=serializer.validated_data["capturas"],
            versao_modelo=serializer.validated_data["versao_modelo"],
            pontuacao_qualidade=serializer.validated_data.get("pontuacao_qualidade", 0.95),
            metadados_origem=serializer.validated_data.get("metadados_origem", {}),
        )
        return Response(
            {
                "perfil": PerfilBiometricoSerializer(perfil, context=self.get_serializer_context()).data,
                "embedding": EmbeddingFacialSerializer(embedding, context=self.get_serializer_context()).data,
            },
            status=status.HTTP_201_CREATED,
        )


class EmbeddingFacialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmbeddingFacial.objects.select_related("perfil", "perfil__aluno").all()
    serializer_class = EmbeddingFacialSerializer
    permission_classes = (IsProfessorOuAdministrador,)
    filterset_fields = ("perfil", "ativo", "status", "versao_modelo")
