"""Clientes para interactuar con la Supabase Admin API."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class SupabaseAdminError(Exception):
    """Error genérico cuando la Supabase Admin API responde con fallo."""

    def __init__(self, message: str, *, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class SupabaseAdminClient:
    """Cliente minimalista para la Supabase Admin API usando urllib."""

    def __init__(self, base_url: str, service_role_key: str, timeout: float = 10.0):
        if not base_url:
            raise SupabaseAdminError('No se configuró SUPABASE_API_URL.')
        self.base_url = base_url.rstrip('/')

        if not service_role_key:
            raise SupabaseAdminError('No se configuró SUPABASE_SERVICE_ROLE_KEY.')
        self.service_role_key = service_role_key
        self.timeout = timeout

    def create_user(
        self,
        *,
        email: str,
        password: str,
        email_confirm: bool = False,
        user_metadata: Optional[Dict[str, Any]] = None,
        app_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Invoca POST /auth/v1/admin/users y retorna el payload JSON."""

        payload: Dict[str, Any] = {
            'email': email,
            'password': password,
            'email_confirm': email_confirm,
        }

        if user_metadata:
            payload['user_metadata'] = user_metadata

        if app_metadata:
            payload['app_metadata'] = app_metadata

        request = Request(
            self._build_url('/auth/v1/admin/users'),
            data=json.dumps(payload).encode('utf-8'),
            method='POST',
        )
        request.add_header('Content-Type', 'application/json')
        request.add_header('apikey', self.service_role_key)
        request.add_header('Authorization', f'Bearer {self.service_role_key}')

        try:
            with urlopen(request, timeout=self.timeout) as response:  # nosec: B310
                response_body = response.read()
        except HTTPError as error:  # pragma: no cover - branches exercised via tests
            raise SupabaseAdminError(
                self._extract_error_message(error),
                status_code=error.code,
            ) from error
        except URLError as error:  # pragma: no cover - network failure handling
            raise SupabaseAdminError(
                f'No se pudo contactar Supabase Admin API: {error.reason}',
            ) from error

        if not response_body:
            return {}

        try:
            return json.loads(response_body.decode('utf-8'))
        except json.JSONDecodeError as error:
            raise SupabaseAdminError(
                'Respuesta inválida de Supabase al crear el usuario.',
            ) from error

    def _build_url(self, path: str) -> str:
        if not path.startswith('/'):
            path = f'/{path}'
        return f'{self.base_url}{path}'

    @staticmethod
    def _extract_error_message(error: HTTPError) -> str:
        body = ''
        try:
            body = error.read().decode('utf-8')
        except Exception:  # pragma: no cover - fallback when body not readable
            body = ''

        if not body:
            return f'Supabase devolvió estado HTTP {error.code}.'

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return body

        if isinstance(data, dict):
            for key in ('message', 'error_description', 'error', 'msg'):
                value = data.get(key)
                if value:
                    return str(value)
            return json.dumps(data)

        return str(data)


def get_supabase_admin_client() -> SupabaseAdminClient:
    """Construye un cliente usando la configuración de settings."""

    base_url = getattr(settings, 'SUPABASE_API_URL', None)
    service_role_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)
    timeout = float(getattr(settings, 'SUPABASE_ADMIN_TIMEOUT', 10))
    return SupabaseAdminClient(
        base_url=base_url,
        service_role_key=service_role_key,
        timeout=timeout,
    )

