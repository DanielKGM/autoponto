from django.utils import timezone
from rest_framework import authentication, exceptions

from api.models import TokenNoBorda


class EdgeNodeTokenAuthentication(authentication.BaseAuthentication):
    keyword = "NodeToken"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        token_bruto = None
        if header.startswith(f"{self.keyword} "):
            token_bruto = header.split(" ", 1)[1].strip()
        elif request.headers.get("X-Node-Token"):
            token_bruto = request.headers["X-Node-Token"].strip()

        if not token_bruto:
            return None

        hash_token = TokenNoBorda.gerar_hash(token_bruto)
        try:
            token = TokenNoBorda.objects.select_related("no").get(hash_token=hash_token, ativo=True)
        except TokenNoBorda.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Token do nó inválido.") from exc

        if not token.pode_autenticar():
            raise exceptions.AuthenticationFailed("Token do nó expirado ou inativo.")

        agora = timezone.now()
        token.ultimo_uso_em = agora
        token.save(update_fields=["ultimo_uso_em", "atualizado_em"])
        token.no.ultimo_sync_em = agora
        token.no.save(update_fields=["ultimo_sync_em", "atualizado_em"])
        return token.no, token
