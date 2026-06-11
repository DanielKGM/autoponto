from rest_framework.permissions import BasePermission, SAFE_METHODS

from api.models import NoBorda, PapelUsuario


def _usuario_humano_autenticado(usuario) -> bool:
    return bool(usuario and usuario.is_authenticated and not isinstance(usuario, NoBorda))


class IsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return bool(_usuario_humano_autenticado(request.user) and request.user.papel == PapelUsuario.ADMINISTRADOR)


class IsProfessorOuAdministrador(BasePermission):
    def has_permission(self, request, view):
        return bool(
            _usuario_humano_autenticado(request.user)
            and request.user.papel in {PapelUsuario.PROFESSOR, PapelUsuario.ADMINISTRADOR}
        )


class IsAdministradorOuSomenteLeitura(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return _usuario_humano_autenticado(request.user)
        return bool(_usuario_humano_autenticado(request.user) and request.user.papel == PapelUsuario.ADMINISTRADOR)


class IsNoBorda(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, NoBorda)
