from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.models import Aula, PapelUsuario, RegistroPresenca
from api.permissions import IsProfessorOuAdministrador
from api.selectors import obter_aulas_acessiveis
from api.serializers import AulaSerializer, RegistroPresencaSerializer
from api.services import fechar_chamada_aula
from api.services.errors import AppError


class AulaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Aula.objects.none()
    serializer_class = AulaSerializer
    permission_classes = (IsProfessorOuAdministrador,)
    filterset_fields = ("status", "horario", "data")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Aula.objects.none()
        return obter_aulas_acessiveis(self.request.user)

    @action(detail=True, methods=["post"], url_path="fechar-chamada")
    def fechar_chamada(self, request, pk=None):
        aula = get_object_or_404(
            Aula.objects.select_related("horario", "horario__turma", "horario__turma__disciplina"),
            pk=pk,
        )
        if request.user.papel != PapelUsuario.ADMINISTRADOR:
            if not aula.horario.turma.professores.filter(id=request.user.id).exists():
                raise PermissionDenied("Você não pode fechar chamada desta turma.")
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
