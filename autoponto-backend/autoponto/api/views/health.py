from django.db import connections
from django.db.utils import OperationalError
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        responses=inline_serializer(
            name="HealthResponse",
            fields={"status": serializers.CharField()},
        )
    )
    def get(self, request):
        return Response({"status": "ok"})


class ReadinessCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    @extend_schema(
        responses=inline_serializer(
            name="ReadinessResponse",
            fields={
                "status": serializers.CharField(),
                "checks": inline_serializer(
                    name="ReadinessChecks",
                    fields={"database": serializers.CharField()},
                ),
            },
        )
    )
    def get(self, request):
        try:
            connections["default"].cursor()
            database = "ok"
            status_code = 200
        except OperationalError:
            database = "error"
            status_code = 503
        return Response({"status": "ok" if database == "ok" else "degraded", "checks": {"database": database}}, status=status_code)
