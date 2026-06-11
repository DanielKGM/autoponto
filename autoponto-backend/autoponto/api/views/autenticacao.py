from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer


def _parametros_cookie_refresh() -> dict:
    return {
        "key": settings.JWT_REFRESH_COOKIE_NAME,
        "path": settings.JWT_REFRESH_COOKIE_PATH,
        "secure": settings.JWT_REFRESH_COOKIE_SECURE,
        "httponly": True,
        "samesite": settings.JWT_REFRESH_COOKIE_SAMESITE,
    }


def _definir_cookie_refresh(response: Response, refresh: str) -> None:
    response.set_cookie(
        value=refresh,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        **_parametros_cookie_refresh(),
    )


def _limpar_cookie_refresh(response: Response) -> None:
    response.delete_cookie(
        key=settings.JWT_REFRESH_COOKIE_NAME,
        path=settings.JWT_REFRESH_COOKIE_PATH,
        samesite=settings.JWT_REFRESH_COOKIE_SAMESITE,
    )


class TokenObtainCookieView(APIView):
    permission_classes = ()
    authentication_classes = ()
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = TokenObtainPairSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        dados = dict(serializer.validated_data)
        refresh = dados.pop("refresh")
        response = Response(dados, status=status.HTTP_200_OK)
        _definir_cookie_refresh(response, refresh)
        return response


class TokenRefreshCookieView(APIView):
    permission_classes = ()
    authentication_classes = ()
    throttle_scope = "auth_refresh"

    def post(self, request):
        refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE_NAME)
        if not refresh:
            return Response({"refresh": "Cookie de refresh ausente."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TokenRefreshSerializer(data={"refresh": refresh}, context={"request": request})
        serializer.is_valid(raise_exception=True)
        dados = dict(serializer.validated_data)
        novo_refresh = dados.pop("refresh", None)
        response = Response(dados, status=status.HTTP_200_OK)
        if novo_refresh:
            _definir_cookie_refresh(response, novo_refresh)
        return response


class LogoutCookieView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _limpar_cookie_refresh(response)
        return response
