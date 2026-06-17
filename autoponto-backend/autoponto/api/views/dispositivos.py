from rest_framework.decorators import action
from rest_framework.response import Response

from api.models import DispositivoEsp32, NoBorda
from api.permissions import IsAdministrador
from api.serializers import DispositivoEsp32Serializer, NoBordaSerializer, TokenNoBordaEmitirSerializer
from .mixins import AdminReadableModelViewSet


class NoBordaViewSet(AdminReadableModelViewSet):
    queryset = NoBorda.objects.all()
    serializer_class = NoBordaSerializer
    filterset_fields = ("ativo",)
    search_fields = ("codigo", "nome", "interscity_uuid")

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdministrador],
        serializer_class=TokenNoBordaEmitirSerializer,
        url_path="emitir-token",
    )
    def emitir_token(self, request, pk=None):
        no = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token, token_bruto = no.tokens.model.emitir_token(
            no=no,
            nome=serializer.validated_data["nome"],
            expira_em=serializer.validated_data.get("expira_em"),
        )
        return Response(
            {
                "token_id": str(token.id),
                "no_id": str(no.id),
                "token": token_bruto,
                "prefixo_token": token.prefixo_token,
            }
        )


class DispositivoEsp32ViewSet(AdminReadableModelViewSet):
    queryset = DispositivoEsp32.objects.select_related("no", "sala", "sala__predio").all()
    serializer_class = DispositivoEsp32Serializer
    filterset_fields = ("no", "sala", "ativo", "status")
    search_fields = ("codigo", "nome", "interscity_uuid")

    @action(detail=False, methods=["get"], permission_classes=[IsAdministrador], url_path="status-dashboard")
    def status_dashboard(self, request):
        dispositivos = self.get_queryset().order_by("codigo")
        payload = []
        for dispositivo in dispositivos:
            payload.append(
                {
                    "id": str(dispositivo.id),
                    "codigo": dispositivo.codigo,
                    "nome": dispositivo.nome,
                    "ativo": dispositivo.ativo,
                    "status": dispositivo.status,
                    "status_efetivo": dispositivo.status_efetivo,
                    "status_atualizado_em": dispositivo.status_atualizado_em.isoformat()
                    if dispositivo.status_atualizado_em
                    else None,
                    "sala": dispositivo.sala.nome if dispositivo.sala else None,
                    "no": dispositivo.no.codigo if dispositivo.no else None,
                    "interscity_uuid": dispositivo.interscity_uuid,
                    "origem_status": "api_local",
                }
            )
        return Response(payload)
