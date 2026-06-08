from rest_framework import viewsets

from api.models import Aula, RegistroPresenca
from api.permissions import IsProfessorOuAdministrador
from api.selectors import obter_aulas_acessiveis
from api.serializers import AulaSerializer, RegistroPresencaSerializer


class AulaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Aula.objects.none()
    serializer_class = AulaSerializer
    permission_classes = (IsProfessorOuAdministrador,)
    filterset_fields = ("status", "horario", "data")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Aula.objects.none()
        return obter_aulas_acessiveis(self.request.user)


class RegistroPresencaViewSet(viewsets.ModelViewSet):
    queryset = RegistroPresenca.objects.select_related("aula", "aluno", "registrado_por_dispositivo").all()
    serializer_class = RegistroPresencaSerializer
    permission_classes = (IsProfessorOuAdministrador,)
    filterset_fields = ("aula", "aluno", "status")
