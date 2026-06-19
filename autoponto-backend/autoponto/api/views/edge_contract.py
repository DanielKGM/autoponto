from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.authentication import EdgeNodeTokenAuthentication
from api.permissions import IsNoBorda
from api.services.sincronizacao_borda import montar_payload_pull, receber_presencas_borda


class EdgePullView(APIView):
    authentication_classes = (EdgeNodeTokenAuthentication,)
    permission_classes = (IsNoBorda,)

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(montar_payload_pull(request.user, request.query_params))


class EdgeAttendanceView(APIView):
    authentication_classes = (EdgeNodeTokenAuthentication,)
    permission_classes = (IsNoBorda,)
    throttle_scope = "edge_attendance"

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        return Response(receber_presencas_borda(request.user, request.data), status=status.HTTP_200_OK)
