from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.authentication import EdgeNodeTokenAuthentication
from api.models import ComandoBorda
from api.permissions import IsNoBorda
from api.services import montar_payload_pull, receber_presencas_borda


class EdgePullView(APIView):
    authentication_classes = (EdgeNodeTokenAuthentication,)
    permission_classes = (IsNoBorda,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(montar_payload_pull(request.user, request.query_params))


class EdgePullSlashAliasView(EdgePullView):
    @extend_schema(exclude=True)
    def get(self, request):
        return super().get(request)


class EdgeAttendanceView(APIView):
    authentication_classes = (EdgeNodeTokenAuthentication,)
    permission_classes = (IsNoBorda,)
    throttle_scope = "edge_attendance"

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        return Response(receber_presencas_borda(request.user, request.data), status=status.HTTP_200_OK)


class EdgeAttendanceSlashAliasView(EdgeAttendanceView):
    @extend_schema(exclude=True)
    def post(self, request):
        return super().post(request)


class EdgeCommandListView(APIView):
    authentication_classes = (EdgeNodeTokenAuthentication,)
    permission_classes = (IsNoBorda,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        node_id = request.query_params.get("node_id")
        if node_id and node_id not in {str(request.user.id), request.user.codigo}:
            return Response({"node_id": "Token do nó não corresponde ao node_id solicitado."}, status=status.HTTP_400_BAD_REQUEST)

        comandos = ComandoBorda.objects.filter(no=request.user, status=ComandoBorda.STATUS_PENDENTE).select_related(
            "dispositivo"
        )
        return Response(
            {
                "commands": [
                    {
                        "id": str(comando.id),
                        "device_id": str(comando.dispositivo_id) if comando.dispositivo_id else None,
                        "type": comando.tipo,
                        "payload": comando.payload,
                        "capability": comando.capacidade,
                        "created_at": comando.criado_em.isoformat(),
                    }
                    for comando in comandos
                ]
            }
        )


class EdgeCommandListSlashAliasView(EdgeCommandListView):
    @extend_schema(exclude=True)
    def get(self, request):
        return super().get(request)


class EdgeCommandAckView(APIView):
    authentication_classes = (EdgeNodeTokenAuthentication,)
    permission_classes = (IsNoBorda,)

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        node_id = request.data.get("node_id")
        if node_id and node_id not in {str(request.user.id), request.user.codigo}:
            return Response({"node_id": "Token do nó não corresponde ao node_id solicitado."}, status=status.HTTP_400_BAD_REQUEST)

        confirmados = []
        for item in request.data.get("commands", []):
            comando = ComandoBorda.objects.filter(id=item.get("id"), no=request.user).first()
            if not comando:
                continue
            try:
                comando.marcar_status(item.get("status", "DELIVERED"), item.get("error", ""))
            except DjangoValidationError as exc:
                return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
            confirmados.append(str(comando.id))
        return Response({"acked_ids": confirmados})


class EdgeCommandAckSlashAliasView(EdgeCommandAckView):
    @extend_schema(exclude=True)
    def post(self, request):
        return super().post(request)
