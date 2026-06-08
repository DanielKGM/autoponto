from rest_framework import viewsets

from api.permissions import IsAdministrador, IsAdministradorOuSomenteLeitura


class AdminModelViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdministrador,)


class AdminReadableModelViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdministradorOuSomenteLeitura,)
