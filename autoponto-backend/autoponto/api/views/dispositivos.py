from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from api.models import DispositivoEsp32, NoBorda, TokenNoBorda
from api.permissions import IsAdministrador
from api.serializers.dispositivos import DispositivoEsp32Serializer, NoBordaSerializer, TokenNoBordaEmitirSerializer
from .mixins import AdminReadableModelViewSet


class NoBordaViewSet(AdminReadableModelViewSet):
    queryset = NoBorda.objects.prefetch_related(
        Prefetch(
            "tokens",
            queryset=TokenNoBorda.objects.filter(ativo=True).order_by("-criado_em"),
            to_attr="tokens_ativos",
        )
    ).all()
    serializer_class = NoBordaSerializer
    filterset_fields = ("ativo",)
    search_fields = ("codigo", "nome")

    def perform_destroy(self, instance):
        with transaction.atomic():
            instance.ativo = False
            instance.save(update_fields=["ativo", "atualizado_em"])
            instance.tokens.filter(ativo=True).update(ativo=False, atualizado_em=timezone.now())

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
        nome = serializer.validated_data["nome"]
        with transaction.atomic():
            token, token_bruto = no.tokens.model.emitir_token(
                no=no,
                nome=nome,
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
    filterset_fields = ("no", "sala", "ativo")
    search_fields = ("codigo", "nome", "interscity_uuid")

    def perform_destroy(self, instance):
        instance.ativo = False
        instance.save(update_fields=["ativo", "atualizado_em"])
