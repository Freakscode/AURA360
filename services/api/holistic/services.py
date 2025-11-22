from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Iterable

import requests
from django.conf import settings
from django.db import connection, transaction
from requests import RequestException, Timeout

from .models import (
    HolisticAgentRun,
    HolisticAgentRunStatus,
    HolisticRequest,
    HolisticVectorQuery,
)

logger = logging.getLogger(__name__)

__all__ = [
    "fetch_user_profile",
    "call_agent_service",
    "create_agent_run",
    "persist_vector_queries",
]


def fetch_user_profile(user_id: str) -> dict[str, Any]:
    """
    Recupera el perfil del usuario desde el modelo AppUser o devuelve un placeholder.

    TODO(@backend): integrar con el servicio real de perfilamiento tan pronto esté disponible.
    """
    profile: dict[str, Any] = {
        "id": user_id,
        "tier": "unknown",
        "locale": "es-MX",
        "preferences": {},
    }

    try:
        from users.models import AppUser  # Importación diferida para evitar ciclos
    except Exception as exc:  # pragma: no cover - import errors should be visible en logs
        logger.warning("No se pudo importar AppUser para obtener perfil: %s", exc)
        return profile

    try:
        tables = connection.introspection.table_names()  # type: ignore[attr-defined]
        if AppUser._meta.db_table not in tables:
            logger.debug(
                "Tabla app_users no encontrada en la base de datos activa; usando placeholder.",
                extra={"holistic_user_id": user_id},
            )
            return profile
    except Exception as exc:  # pragma: no cover - defensivo ante introspección fallida
        logger.warning(
            "No se pudo verificar la existencia de app_users.",
            extra={"holistic_user_id": user_id},
            exc_info=exc,
        )
        return profile

    try:
        auth_uuid = uuid.UUID(user_id)
    except ValueError:
        auth_uuid = None

    user_data: dict[str, Any] | None = None
    try:
        user_query = AppUser.objects.all()

        if auth_uuid is not None:
            user_data = user_query.filter(auth_user_id=auth_uuid).values(
                "auth_user_id",
                "full_name",
                "email",
                "tier",
                "role_global",
                "gender",
                "age",
                "phone_number",
            ).first()

        if user_data is None:
            try:
                numeric_id = int(user_id)
            except (ValueError, TypeError):
                numeric_id = None

            if numeric_id is not None:
                user_data = user_query.filter(pk=numeric_id).values(
                    "auth_user_id",
                    "full_name",
                    "email",
                    "tier",
                    "role_global",
                    "gender",
                    "age",
                    "phone_number",
                ).first()
    except Exception as exc:  # pragma: no cover - defensivo ante esquema no sincronizado
        logger.warning(
            "No se pudo consultar AppUser para construir perfil.",
            extra={"holistic_user_id": user_id},
            exc_info=exc,
        )
        return profile

    if user_data is None:
        logger.info(
            "Perfil de usuario no encontrado, usando placeholder.",
            extra={"holistic_user_id": user_id},
        )
        return profile

    profile.update(
        {
            "auth_user_id": str(user_data.get("auth_user_id")),
            "full_name": user_data.get("full_name"),
            "email": user_data.get("email"),
            "tier": user_data.get("tier"),
            "role": user_data.get("role_global"),
            "gender": user_data.get("gender"),
            "age": user_data.get("age"),
            "phone_number": user_data.get("phone_number"),
        }
    )
    return profile


def call_agent_service(payload: dict[str, Any], trace_id: str, timeout: int = 120) -> dict[str, Any]:
    """
    Invoca al servicio de agentes holísticos y normaliza la respuesta.

    Retorna un diccionario con la forma:
    {
        "status": "success|error",
        "status_code": int | None,
        "data": dict | None,
        "error": dict | None,
        "latency_ms": int | None,
    }
    """
    service_url = getattr(settings, "HOLISTIC_AGENT_SERVICE_URL", "")
    service_token = getattr(settings, "HOLISTIC_AGENT_SERVICE_TOKEN", None)

    if not service_url:
        logger.error(
            "HOLISTIC_AGENT_SERVICE_URL no configurado.",
            extra={"trace_id": trace_id},
        )
        return {
            "status": "error",
            "status_code": None,
            "data": None,
            "error": {
                "type": "configuration_error",
                "message": "HOLISTIC_AGENT_SERVICE_URL no está configurado.",
            },
            "latency_ms": None,
        }

    headers = {
        "Content-Type": "application/json",
        "X-Trace-Id": str(trace_id),
    }
    if service_token:
        headers["Authorization"] = f"Bearer {service_token}"

    try:
        start_time = time.monotonic()
        response = requests.post(
            service_url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        latency_ms = int((time.monotonic() - start_time) * 1000)
    except Timeout as exc:
        logger.warning(
            "Timeout al invocar servicio de agentes.",
            extra={"trace_id": trace_id, "error": str(exc)},
        )
        return {
            "status": "error",
            "status_code": None,
            "data": None,
            "error": {
                "type": "timeout",
                "message": "La llamada al servicio de agentes expiró.",
            },
            "latency_ms": timeout * 1000,
        }
    except RequestException as exc:
        logger.error(
            "Error de red al invocar servicio de agentes.",
            extra={"trace_id": trace_id, "error": str(exc)},
        )
        return {
            "status": "error",
            "status_code": None,
            "data": None,
            "error": {
                "type": "request_exception",
                "message": str(exc),
            },
            "latency_ms": None,
        }

    status_code = response.status_code

    try:
        response.raise_for_status()
    except RequestException as exc:
        logger.warning(
            "El servicio de agentes devolvió error HTTP.",
            extra={
                "trace_id": trace_id,
                "status_code": status_code,
                "error": str(exc),
            },
        )
        error_payload: dict[str, Any]
        try:
            error_payload = response.json()
        except ValueError:
            error_payload = {"raw_body": response.text}
        return {
            "status": "error",
            "status_code": status_code,
            "data": None,
            "error": {
                "type": "response_error",
                "message": str(exc),
                "payload": error_payload,
            },
            "latency_ms": latency_ms,
        }

    try:
        data = response.json()
    except ValueError as exc:
        logger.error(
            "El servicio de agentes devolvió JSON inválido.",
            extra={"trace_id": trace_id, "status_code": status_code},
        )
        return {
            "status": "error",
            "status_code": status_code,
            "data": None,
            "error": {
                "type": "invalid_json",
                "message": str(exc),
            },
            "latency_ms": latency_ms,
        }

    return {
        "status": "success",
        "status_code": status_code,
        "data": data,
        "error": None,
        "latency_ms": latency_ms,
    }


@transaction.atomic
def create_agent_run(
    holistic_request: HolisticRequest,
    *,
    agent_name: str,
    status: str,
    input_context: dict[str, Any] | None = None,
    output_payload: dict[str, Any] | None = None,
    latency_ms: int | None = None,
    error_type: str | None = None,
) -> HolisticAgentRun:
    """
    Crea un registro HolisticAgentRun asociado a una solicitud.

    Devuelve la instancia creada para facilitar el encadenamiento con persist_vector_queries.
    """
    return HolisticAgentRun.objects.create(
        request=holistic_request,
        agent_name=agent_name,
        status=status,
        latency_ms=latency_ms,
        input_context=input_context or {},
        output_payload=output_payload or {},
        error_type=error_type,
    )


def persist_vector_queries(
    agent_run: HolisticAgentRun,
    queries: Iterable[dict[str, Any]],
) -> list[HolisticVectorQuery]:
    """
    Persiste las consultas vectoriales reportadas por el agente.

    Cada elemento de `queries` debe contener al menos:
    - vector_store
    - embedding_model
    - query_text
    Opcionalmente:
    - top_k
    - response_payload
    - confidence_score
    """
    stored_queries: list[HolisticVectorQuery] = []
    for query in queries or []:
        stored_queries.append(
            HolisticVectorQuery.objects.create(
                agent_run=agent_run,
                vector_store=query.get("vector_store", ""),
                embedding_model=query.get("embedding_model", ""),
                query_text=query.get("query_text", ""),
                top_k=query.get("top_k") or 5,
                response_payload=query.get("response_payload") or {},
                confidence_score=query.get("confidence_score"),
            )
        )
    return stored_queries