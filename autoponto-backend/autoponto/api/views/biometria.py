from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import EmbeddingFacial, PapelUsuario, PerfilBiometrico, Usuario
from api.permissions import IsAdministrador
from api.serializers.biometria import EmbeddingFacialSerializer, MatriculaBiometricaSerializer, PerfilBiometricoSerializer
from api.services.biometria import matricular_biometria_aluno
from api.services.errors import AppError
from .mixins import AdminReadableModelViewSet


class PerfilBiometricoViewSet(AdminReadableModelViewSet):
    queryset = PerfilBiometrico.objects.select_related("aluno").all()
    serializer_class = PerfilBiometricoSerializer
    filterset_fields = ("status", "aluno")
    throttle_scope = "biometria"

    def filtrar_queryset_por_usuario(self, queryset, usuario):
        if getattr(usuario, "papel", None) == PapelUsuario.ALUNO:
            return queryset.filter(aluno=usuario)
        return queryset.none()

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
        try:
            perfil, embedding = matricular_biometria_aluno(
                aluno=aluno,
                capturas=serializer.validated_data["capturas"],
                versao_modelo=serializer.validated_data["versao_modelo"],
            )
        except AppError as erro:
            corpo = {"detail": erro.message, "code": erro.code}
            corpo.update(erro.extra)
            return Response(corpo, status=erro.status_code)
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
    permission_classes = (IsAdministrador,)
    filterset_fields = ("perfil", "ativo", "status", "versao_modelo")
