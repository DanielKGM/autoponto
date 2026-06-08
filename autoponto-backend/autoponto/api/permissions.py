from rest_framework.permissions import BasePermission, SAFE_METHODS

from api.models import NoBorda, PapelUsuario


class IsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.papel == PapelUsuario.ADMINISTRADOR)


class IsProfessorOuAdministrador(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.papel in {PapelUsuario.PROFESSOR, PapelUsuario.ADMINISTRADOR}
        )


class IsAdministradorOuSomenteLeitura(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.papel == PapelUsuario.ADMINISTRADOR)


class IsNoBorda(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.user, NoBorda)
