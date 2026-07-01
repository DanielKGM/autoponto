from time import perf_counter

from rest_framework import viewsets

from api.permissions import IsAdministrador, IsAdministradorOuSomenteLeitura
from api.services.tcc_metricas import registrar_tempo


class MetricasEndpointMixin:
    metrica_endpoint = ""
    servico_metricas = "servidor-principal"

    def dispatch(self, request, *args, **kwargs):
        inicio = perf_counter()
        try:
            response = super().dispatch(request, *args, **kwargs)
        except Exception:
            self._registrar_tempo_endpoint(
                request,
                inicio,
                status="falha",
                status_code=None,
            )
            raise

        status_code = getattr(response, "status_code", None)
        status = "sucesso" if status_code is not None and status_code < 500 else "falha"
        self._registrar_tempo_endpoint(
            request,
            inicio,
            status=status,
            status_code=status_code,
        )
        return response

    def _registrar_tempo_endpoint(self, request, inicio: float, status: str, status_code):
        if not self.metrica_endpoint:
            return
        registrar_tempo(
            self.metrica_endpoint,
            (perf_counter() - inicio) * 1000,
            servico=self.servico_metricas,
            status=status,
            origem=self.__class__.__name__,
            detalhes={
                "metodo": getattr(request, "method", ""),
                "path": getattr(request, "path", ""),
                "status_code": status_code,
            },
        )


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
