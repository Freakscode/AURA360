from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from confluent_kafka import Producer
import redis

from agents_service.api.dependencies import get_holistic_service
from infra.env import load_environment
from services.exceptions import ServiceError
from services.holistic import AdviceRequest, HolisticAdviceService

router = APIRouter(tags=["holistic-advice"])

logger = logging.getLogger(__name__)

load_environment(override=False)


class AdvicePreferences(BaseModel):
    """Preferencias opcionales para personalizar las recomendaciones."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
    )

    focus: list[str] | str | None = Field(
        default=None,
        description="Áreas prioritarias declaradas por la persona (ej: ['respiración', 'ejercicio']).",
    )
    intensity_level: str | None = Field(
        default=None,
        description="Nivel de intensidad deseado: 'low', 'medium', 'high'.",
    )
    schedule_constraints: list[str] | None = Field(
        default=None,
        description="Restricciones de horario o disponibilidad.",
    )


class AdviceRequestPayload(BaseModel):
    """Payload de solicitud para generar recomendaciones holísticas."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
    )

    trace_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único de trazabilidad generado por el backend.",
        examples=["trace-2024-abc123"],
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Categoría solicitada: mind, body, soul o holistic.",
        examples=["mind", "holistic"],
    )
    user_profile: dict[str, Any] = Field(
        ...,
        min_length=1,
        description="Perfil estructurado de la persona con información relevante.",
        examples=[{"id": "user-123", "name": "Ana", "age": 30}],
    )
    preferences: AdvicePreferences | dict[str, Any] | None = Field(
        default=None,
        description="Preferencias opcionales que guían la recomendación.",
    )
    context: Any | None = Field(
        default=None,
        description="Contexto adicional textual o estructurado sobre la situación actual.",
    )

    @field_validator("user_profile")
    @classmethod
    def _ensure_user_profile(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not value:
            raise ValueError("user_profile no puede ser vacío.")
        return value

    @field_validator("trace_id")
    @classmethod
    def _ensure_trace_id(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("trace_id es obligatorio.")
        return value

    @field_validator("category")
    @classmethod
    def _normalize_category(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("category es obligatorio.")
        return normalized


class AdviceResponsePayload(BaseModel):
    """Respuesta estructurada del servicio de recomendaciones holísticas."""

    model_config = ConfigDict(
        use_enum_values=True,
    )

    status: str = Field(
        ...,
        description="Estado de la respuesta: 'success' o 'error'.",
        examples=["success"],
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Datos de respuesta cuando la operación es exitosa.",
    )
    error: dict[str, Any] | None = Field(
        default=None,
        description="Información del error cuando la operación falla.",
    )
    meta: dict[str, Any] = Field(
        ...,
        description="Metadatos de la respuesta (trace_id, timestamp, versión).",
    )


@router.post(
    "/advice",
    response_model=AdviceResponsePayload,
    status_code=status.HTTP_200_OK,
    summary="Genera recomendaciones holísticas para una persona",
)
def holistic_advice_endpoint(
    payload: AdviceRequestPayload,
    service: HolisticAdviceService = Depends(get_holistic_service),
) -> AdviceResponsePayload:
    preferences: dict[str, Any] | None
    if isinstance(payload.preferences, AdvicePreferences):
        preferences = payload.preferences.model_dump(exclude_none=True)
    elif isinstance(payload.preferences, dict):
        preferences = {key: value for key, value in payload.preferences.items() if value is not None}
    else:
        preferences = None

    request = AdviceRequest(
        trace_id=payload.trace_id,
        category=payload.category,
        user_profile=payload.user_profile,
        preferences=preferences,
        context=payload.context,
    )

    try:
        response = service.generate_advice(request)
        return AdviceResponsePayload(**response)
    except ServiceError as exc:
        logger.warning(
            "holistic_advice_endpoint: error del servicio",
            extra={"trace_id": payload.trace_id, "error_type": exc.error.type},
        )
        body = exc.to_response(trace_id=payload.trace_id)
        return JSONResponse(status_code=exc.status_code, content=body)
    except Exception as exc:
        logger.exception(
            "holistic_advice_endpoint: error inesperado",
            extra={"trace_id": payload.trace_id},
        )
        body = {
            "status": "error",
            "data": None,
            "error": {
                "type": "unhandled_error",
                "message": "Error inesperado procesando la solicitud.",
            },
            "meta": {
                "trace_id": payload.trace_id,
                "model_version": service.settings.model_version,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=body)


# ============================================================================
# ASYNC GUARDIAN REQUEST-REPLY PATTERN
# ============================================================================


class AsyncAdviceRequestPayload(BaseModel):
    """Payload for async Guardian advice request via Kafka."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
    )

    trace_id: str = Field(
        ...,
        min_length=1,
        description="Identificador único de trazabilidad.",
        examples=["trace-2024-abc123"],
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Categoría solicitada: mind, body, soul o holistic.",
        examples=["mind", "holistic"],
    )
    user_id: str = Field(
        ...,
        min_length=1,
        description="ID del usuario.",
    )
    query: str = Field(
        ...,
        min_length=1,
        description="Consulta o pregunta del usuario.",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Contexto adicional (user_profile, preferences, etc.).",
    )


class AsyncAdviceResponsePayload(BaseModel):
    """Response for async request containing request_id for polling."""

    model_config = ConfigDict(use_enum_values=True)

    status: str = Field(default="accepted")
    request_id: str = Field(..., description="ID para consultar el estado de la solicitud.")
    message: str = Field(default="Solicitud aceptada y en procesamiento")
    poll_url: str = Field(..., description="URL para consultar el resultado")
    meta: dict[str, Any] = Field(default_factory=dict)


# Kafka Producer singleton
_kafka_producer: Optional[Producer] = None


def get_kafka_producer() -> Producer:
    """Get or create Kafka producer."""
    global _kafka_producer
    if _kafka_producer is None:
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        producer_config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": f"guardian-api-producer-{os.getpid()}",
            "acks": "all",
            "retries": 3,
            "enable.idempotence": True,
        }
        _kafka_producer = Producer(producer_config)
        logger.info(f"Kafka producer initialized: {bootstrap_servers}")
    return _kafka_producer


# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client for response storage."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        logger.info(f"Redis client initialized: {redis_url}")
    return _redis_client


@router.post(
    "/advice/async",
    response_model=AsyncAdviceResponsePayload,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicita recomendaciones holísticas de forma asíncrona (Kafka)",
)
def holistic_advice_async_endpoint(
    payload: AsyncAdviceRequestPayload,
) -> AsyncAdviceResponsePayload:
    """
    Publica GuardianRequestEvent a Kafka y retorna request_id para polling.

    Este endpoint es no-bloqueante. El usuario debe usar el request_id para
    consultar el estado del procesamiento en el endpoint /advice/async/{request_id}.
    """
    request_id = str(uuid4())
    trace_id = payload.trace_id

    logger.info(
        f"Async Guardian request received",
        extra={
            "request_id": request_id,
            "trace_id": trace_id,
            "user_id": payload.user_id,
            "category": payload.category,
        },
    )

    try:
        # Map category to guardian_type
        category_to_guardian = {
            "mind": "mental",
            "body": "physical",
            "soul": "spiritual",
            "holistic": "holistic",
        }
        guardian_type = category_to_guardian.get(payload.category.lower(), "holistic")

        # Build GuardianRequestEvent
        event = {
            "event_type": "guardian.request",
            "event_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "user_id": payload.user_id,
            "guardian_type": guardian_type,
            "request_id": request_id,
            "query": payload.query,
            "context": payload.context,
        }

        # Publish to Kafka
        producer = get_kafka_producer()
        producer.produce(
            topic="aura360.guardian.requests",
            key=request_id,
            value=json.dumps(event).encode("utf-8"),
            headers={
                "event_type": "guardian.request",
                "request_id": request_id,
                "trace_id": trace_id,
            },
        )
        producer.flush(timeout=5)

        logger.info(
            f"GuardianRequestEvent published to Kafka",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "topic": "aura360.guardian.requests",
            },
        )

        return AsyncAdviceResponsePayload(
            status="accepted",
            request_id=request_id,
            message="Solicitud aceptada y en procesamiento",
            poll_url=f"/api/v1/holistic/advice/async/{request_id}",
            meta={
                "trace_id": trace_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as exc:
        logger.error(
            f"Error publishing GuardianRequestEvent: {exc}",
            exc_info=True,
            extra={"request_id": request_id, "trace_id": trace_id},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Error al publicar la solicitud",
                "error": str(exc),
            },
        )


@router.get(
    "/advice/async/{request_id}",
    summary="Consulta el estado de una solicitud asíncrona",
)
def get_async_advice_status(
    request_id: str,
    timeout: int = Query(default=0, ge=0, le=30, description="Tiempo de espera en segundos (0 = no esperar)"),
) -> JSONResponse:
    """
    Consulta el estado de una solicitud asíncrona usando request_id.

    - Si timeout=0: Retorna inmediatamente con el estado actual.
    - Si timeout>0: Espera hasta timeout segundos por una respuesta.

    Estados posibles:
    - pending: La solicitud está en procesamiento.
    - completed: La respuesta está disponible.
    - error: Ocurrió un error durante el procesamiento.
    - not_found: No se encontró la solicitud (puede haber expirado).
    """
    redis_client = get_redis_client()
    redis_key = f"guardian:response:{request_id}"

    try:
        # Check if response exists in Redis
        response_data = redis_client.get(redis_key)

        if response_data:
            response = json.loads(response_data)
            logger.info(
                f"Guardian response found in Redis",
                extra={"request_id": request_id},
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "completed",
                    "request_id": request_id,
                    "data": response,
                },
            )

        # If timeout > 0, poll with exponential backoff
        if timeout > 0:
            import time

            elapsed = 0
            interval = 0.5  # Start with 500ms

            while elapsed < timeout:
                time.sleep(interval)
                elapsed += interval

                response_data = redis_client.get(redis_key)
                if response_data:
                    response = json.loads(response_data)
                    logger.info(
                        f"Guardian response found after {elapsed}s",
                        extra={"request_id": request_id, "elapsed": elapsed},
                    )
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content={
                            "status": "completed",
                            "request_id": request_id,
                            "data": response,
                        },
                    )

                # Exponential backoff (max 2s)
                interval = min(interval * 1.5, 2.0)

        # No response found
        logger.info(
            f"Guardian response not ready",
            extra={"request_id": request_id, "timeout": timeout},
        )
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "pending",
                "request_id": request_id,
                "message": "La solicitud está en procesamiento",
            },
        )

    except Exception as exc:
        logger.error(
            f"Error retrieving Guardian response: {exc}",
            exc_info=True,
            extra={"request_id": request_id},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "request_id": request_id,
                "message": "Error al consultar el estado",
                "error": str(exc),
            },
        )