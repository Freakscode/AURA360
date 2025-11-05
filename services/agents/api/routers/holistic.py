from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

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