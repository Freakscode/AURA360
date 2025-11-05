"""Permisos personalizados para validar tokens de servicio."""

from rest_framework.permissions import BasePermission, SAFE_METHODS


def _has_valid_bearer(request) -> bool:
    """Valida que exista un bearer token y un usuario autenticado."""

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False

    token = auth_header.split(' ', 1)[1].strip()
    if not token:
        return False

    user = getattr(request, 'user', None)
    return bool(user and getattr(user, 'is_authenticated', False))


class SupabaseJWTOptionalPermission(BasePermission):
    """Permite lecturas públicas, exige Bearer + autenticación para mutaciones."""

    message = 'Se requiere autenticación Bearer válida para realizar esta operación.'

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return _has_valid_bearer(request)


class SupabaseJWTRequiredPermission(BasePermission):
    """Exige siempre un Bearer token válido."""

    message = 'Debes autenticarte con un token Bearer emitido por Supabase.'

    def has_permission(self, request, view):
        return _has_valid_bearer(request)


class SupabaseServiceRolePermission(BasePermission):
    """Permite únicamente tokens firmados con el rol service_role."""

    message = 'Esta operación requiere un token con rol service_role emitido por Supabase.'

    def has_permission(self, request, view):
        if not _has_valid_bearer(request):
            return False
        user = getattr(request, 'user', None)
        role = getattr(user, 'role', None)
        if role is None:
            return False
        return str(role).lower() == 'service_role'
