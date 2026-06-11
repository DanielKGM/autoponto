from rest_framework import viewsets

from api.permissions import IsAdministrador, IsAdministradorOuSomenteLeitura


class AdminModelViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdministrador,)


class AdminReadableModelViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdministradorOuSomenteLeitura,)

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario = self.request.user
        if getattr(usuario, "papel", None) == "ADMINISTRADOR":
            return queryset
        return self.filtrar_queryset_por_usuario(queryset, usuario)

    def filtrar_queryset_por_usuario(self, queryset, usuario):
        return queryset.none()
