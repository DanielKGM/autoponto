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
    search_fields = ("codigo", "nome", "versao_software", "interscity_uuid")

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
    queryset = DispositivoEsp32.objects.select_related("no", "sala").all()
    serializer_class = DispositivoEsp32Serializer
    filterset_fields = ("no", "sala", "ativo")
    search_fields = ("codigo", "nome", "versao_firmware", "interscity_uuid")
