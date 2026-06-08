from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsAdministrador
from api.services import criar_comando_por_interscity
from api.services.interscity import ClienteInterSCity


class InterSCityActuatorWebhookView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        if request.data.get("action") != "actuator_command":
            return Response({"detail": "Ação de webhook não suportada."}, status=status.HTTP_400_BAD_REQUEST)
        comando = criar_comando_por_interscity(request.data.get("command", {}))
        return Response({"command_id": str(comando.id), "status": comando.status}, status=status.HTTP_202_ACCEPTED)


class InterSCityDiagnosticoView(APIView):
    permission_classes = (IsAdministrador,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(ClienteInterSCity().diagnosticar_servicos())
