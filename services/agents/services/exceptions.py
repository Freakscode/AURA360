from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Optional

from infra import ServiceSettings, get_settings


@dataclass(slots=True)
class ErrorDetails:
    """Representa la estructura de error para respuestas del API."""

    type: str
    message: str
    details: Any = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type, "message": self.message}
        if self.details is not None:
            payload["details"] = self.details
        return payload


class ServiceError(Exception):
    """Error base para el dominio del servicio de agentes."""

    status_code: int = 500

    def __init__(self, *, error_type: str, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.error = ErrorDetails(type=error_type, message=message, details=details)

    def to_response(self, *, trace_id: str, settings: Optional[ServiceSettings] = None) -> dict[str, Any]:
        resolved_settings = settings or get_settings()
        timestamp = datetime.now(timezone.utc).isoformat()
        return {
            "status": "error",
            "data": None,
            "error": self.error.to_dict(),
            "meta": {
                "trace_id": trace_id,
                "model_version": resolved_settings.model_version,
                "timestamp": timestamp,
            },
        }


class UnsupportedCategoryError(ServiceError):
    """Señala que la categoría solicitada no está soportada."""

    status_code = 422

    def __init__(self, *, category: str) -> None:
        super().__init__(
            error_type="unsupported_category",
            message="La categoría solicitada no está soportada por el servicio.",
            details={"category": category},
        )


class VectorQueryError(ServiceError):
    """Errores al consultar la base vectorial."""

    status_code = 502

    def __init__(self, *, message: str, details: Any = None) -> None:
        super().__init__(error_type="vector_query_error", message=message, details=details)


class AgentExecutionError(ServiceError):
    """Errores durante la ejecución del pipeline de agentes."""

    status_code = 500

    def __init__(self, *, message: str, details: Any = None) -> None:
        super().__init__(error_type="agent_execution_error", message=message, details=details)


__all__ = [
    "AgentExecutionError",
    "ErrorDetails",
    "ServiceError",
    "UnsupportedCategoryError",
    "VectorQueryError",
]