from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.models import Aula, PapelUsuario, RegistroPresenca
from api.permissions import IsProfessorOuAdministrador
from api.selectors.presencas import obter_aulas_acessiveis
from api.serializers.presencas import AulaSerializer, RegistroPresencaSerializer
from api.services.aulas import abrir_chamada_aula, fechar_chamada_aula
from api.services.errors import AppError


class AulaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Aula.objects.none()
    serializer_class = AulaSerializer
    permission_classes = (IsProfessorOuAdministrador,)
    filterset_fields = ("status", "turma", "sala", "horario_padrao", "data")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Aula.objects.none()
        return obter_aulas_acessiveis(self.request.user)

    def _obter_aula_com_permissao(self, pk):
        aula = get_object_or_404(
            Aula.objects.select_related("turma", "turma__disciplina"),
            pk=pk,
        )
        if self.request.user.papel != PapelUsuario.ADMINISTRADOR:
            if not aula.turma.professores.filter(id=self.request.user.id).exists():
                raise PermissionDenied("Voce nao pode alterar chamada desta turma.")
        return aula

    @action(detail=True, methods=["post"], url_path="abrir-chamada")
    def abrir_chamada(self, request, pk=None):
        aula = self._obter_aula_com_permissao(pk)
        try:
            aula = abrir_chamada_aula(aula)
        except AppError as erro:
            return Response({"detail": erro.message, "code": erro.code}, status=erro.status_code)
        return Response(AulaSerializer(aula, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], url_path="fechar-chamada")
    def fechar_chamada(self, request, pk=None):
        aula = self._obter_aula_com_permissao(pk)
        try:
            aula = fechar_chamada_aula(aula, request.user)
        except AppError as erro:
            return Response({"detail": erro.message, "code": erro.code}, status=erro.status_code)
        return Response(AulaSerializer(aula, context=self.get_serializer_context()).data)


class RegistroPresencaViewSet(viewsets.ModelViewSet):
    queryset = RegistroPresenca.objects.select_related("aula", "aluno", "registrado_por_dispositivo").all()
    serializer_class = RegistroPresencaSerializer
    permission_classes = (IsProfessorOuAdministrador,)
    filterset_fields = ("aula", "aluno", "status")

    def get_queryset(self):
        queryset = super().get_queryset()
        if getattr(self.request.user, "papel", None) == PapelUsuario.ADMINISTRADOR:
            return queryset
        return queryset.filter(aula__turma__professores=self.request.user).distinct()

    def _exigir_admin_para_escrita(self):
        if self.request.user.papel != PapelUsuario.ADMINISTRADOR:
            raise PermissionDenied("Apenas administradores podem alterar presenças diretamente.")

    def perform_create(self, serializer):
        self._exigir_admin_para_escrita()
        serializer.save()

    def perform_update(self, serializer):
        self._exigir_admin_para_escrita()
        serializer.save()

    def perform_destroy(self, instance):
        self._exigir_admin_para_escrita()
        instance.delete()
