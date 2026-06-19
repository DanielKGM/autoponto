from rest_framework import viewsets

from api.models import Usuario
from api.permissions import IsAdministrador
from api.serializers.identidade import UsuarioSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by("username")
    serializer_class = UsuarioSerializer
    permission_classes = (IsAdministrador,)
    filterset_fields = ("papel", "is_active")
    search_fields = ("username", "email", "nome_completo", "matricula")
