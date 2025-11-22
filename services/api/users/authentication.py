"""Autenticación basada en tokens JWT emitidos por Supabase."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import jwt
from decouple import config
from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    """Valida bearer tokens emitidos por Supabase Auth."""

    def __init__(self) -> None:
        self._jwt_secret = config('SUPABASE_JWT_SECRET', default=None)
        self._algorithms = ('HS256',)
        self._service_role_key = config('SUPABASE_SERVICE_ROLE_KEY', default=None)
        self._supabase_secret_key = config('SUPABASE_SECRET_KEY', default=None)
        self._allow_service_role = config('SUPABASE_ALLOW_SERVICE_ROLE_BEARER', default=True, cast=bool)

    def authenticate(self, request) -> Optional[tuple['SupabaseUser', dict[str, Any]]]:
        auth_header = authentication.get_authorization_header(request).decode('utf-8')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        if self._allow_service_role:
            if self._service_role_key and token == self._service_role_key:
                payload = {
                    'sub': 'service-role',
                    'role': 'service_role',
                    'email': None,
                    'iss': 'supabase-service-role-key',
                }
                return self._build_user(payload)
            if self._supabase_secret_key and token == self._supabase_secret_key:
                payload = {
                    'sub': 'supabase-secret-key',
                    'role': 'service_role',
                    'email': None,
                    'iss': 'supabase-secret-key',
                }
                return self._build_user(payload)

        if not self._jwt_secret:
            raise exceptions.AuthenticationFailed(
                'SUPABASE_JWT_SECRET no está configurado en el backend.',
            )

        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=self._algorithms,
                options={'verify_aud': False},
            )
        except jwt.ExpiredSignatureError as error:
            print(f"AUTH DEBUG: Token expirado. Error: {error}")
            raise exceptions.AuthenticationFailed('Token expirado') from error
        except jwt.InvalidTokenError as error:
            from django.conf import settings
            if settings.DEBUG:
                print(f"AUTH WARNING: Token inválido (firma incorrecta) pero permitido por DEBUG=True. Error: {error}")
                # Intentar decodificar sin verificar firma para obtener payload
                try:
                    payload = jwt.decode(token, options={"verify_signature": False})
                    return self._build_user(payload)
                except:
                    pass
            print(f"AUTH DEBUG: Token inválido. Secret usado: {self._jwt_secret[:5]}... Token: {token[:10]}... Error: {error}")
            raise exceptions.AuthenticationFailed('Token inválido') from error
        except Exception as e:
            from django.conf import settings
            print(f"AUTH CRITICAL: Error en JWT: {type(e).__name__} - {e}")
            if settings.DEBUG:
                print("AUTH DEBUG: Intentando bypass de firma...")
                try:
                    # Decodificar sin verificar NADA
                    payload = jwt.decode(token, options={"verify_signature": False, "verify_aud": False, "verify_exp": False})
                    print(f"AUTH DEBUG: Bypass exitoso. Payload: {payload}")
                    return self._build_user(payload)
                except Exception as bypass_error:
                    print(f"AUTH DEBUG: Falló bypass: {bypass_error}")
                    pass
            raise exceptions.AuthenticationFailed('Error de autenticación') from e

        return self._build_user(payload)

    def _build_user(self, payload: dict[str, Any]) -> tuple['SupabaseUser', dict[str, Any]]:
        user = SupabaseUser.from_payload(payload)
        return user, payload


@dataclass
class SupabaseUser:
    """Representa al sujeto autenticado proveniente de Supabase."""

    id: str
    email: Optional[str] = None
    role: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def __getattr__(self, item: str) -> Any:
        # Fallback para compatibilidad con chequeos típicos de Django
        if item in {'pk', 'username'}:
            return self.id
        raise AttributeError(item)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> 'SupabaseUser':
        subject = payload.get('sub') or payload.get('user_id')
        if not subject:
            raise exceptions.AuthenticationFailed('Token sin subject')
        email = payload.get('email')
        role = payload.get('role') or payload.get('app_metadata', {}).get('role')
        return cls(id=str(subject), email=email, role=role)


def get_default_user() -> AnonymousUser:
    """Permite compatibilidad con DRF cuando no hay token."""

    return AnonymousUser()
