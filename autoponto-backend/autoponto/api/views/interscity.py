from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAdministrador
from api.services.interscity import ClienteInterSCity, sincronizar_recursos_iot_interscity


class InterSCityDiagnosticoView(APIView):
    permission_classes = (IsAdministrador,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(ClienteInterSCity().diagnosticar_servicos())


class InterSCitySincronizarRecursosView(APIView):
    permission_classes = (IsAdministrador,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def post(self, request):
        return Response(sincronizar_recursos_iot_interscity())
