"""Servicios auxiliares para ingestión de planes nutricionales."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Iterable

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from requests import RequestException

logger = logging.getLogger(__name__)


class NutritionPlanStorageError(RuntimeError):
    """Errores al almacenar el PDF previo a la ingestión."""


class NutritionPlanIngestionError(RuntimeError):
    """Errores al despachar el trabajo al servicio vectorial."""


@dataclass(slots=True)
class NutritionPlanStorageResult:
    """Resultado del almacenamiento del PDF en el backend configurado."""

    storage_kind: str
    path: str
    bucket: str | None
    public_url: str | None


def _build_storage_key(auth_user_id: str, job_id: uuid.UUID, filename: str | None) -> str:
    prefix = getattr(settings, "NUTRITION_PLAN_STORAGE_PREFIX", "nutrition-plans").strip("/")
    sanitized_filename = (filename or "plan.pdf").rsplit("/", 1)[-1]
    if not sanitized_filename.lower().endswith(".pdf"):
        sanitized_filename = f"{sanitized_filename}.pdf"
    return f"{prefix}/{auth_user_id}/{job_id}/{sanitized_filename}".replace("//", "/")


def store_nutrition_plan_pdf(
    *,
    uploaded_bytes: bytes,
    content_type: str,
    auth_user_id: str,
    job_id: uuid.UUID,
    original_name: str | None = None,
) -> NutritionPlanStorageResult:
    """Persist the uploaded PDF either in Supabase Storage or local storage."""

    bucket = getattr(settings, "NUTRITION_PLAN_STORAGE_BUCKET", None)
    api_url = getattr(settings, "SUPABASE_API_URL", None)
    service_role_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
    storage_timeout = getattr(settings, "NUTRITION_PLAN_STORAGE_TIMEOUT", 15)

    storage_key = _build_storage_key(auth_user_id, job_id, original_name)

    if bucket and api_url and service_role_key:
        object_path = f"{bucket}/{storage_key}".replace("//", "/")
        endpoint = f"{api_url.rstrip('/')}/storage/v1/object/{object_path}"
        headers = {
            "Authorization": f"Bearer {service_role_key}",
            "Content-Type": content_type,
            "X-Upsert": "true",
        }

        try:
            response = requests.post(
                endpoint,
                data=uploaded_bytes,
                headers=headers,
                timeout=storage_timeout,
            )
            response.raise_for_status()
        except RequestException as exc:  # pragma: no cover - network issues
            logger.error(
                "Fallo al subir PDF a Supabase Storage.",
                extra={
                    "auth_user_id": auth_user_id,
                    "endpoint": endpoint,
                    "storage_key": storage_key,
                },
                exc_info=exc,
            )
            raise NutritionPlanStorageError("No se pudo guardar el PDF en Supabase Storage") from exc

        public_base = getattr(settings, "NUTRITION_PLAN_STORAGE_PUBLIC_URL", None)
        public_url = None
        if public_base:
            public_url = f"{public_base.rstrip('/')}/{storage_key}".replace("//", "/")

        return NutritionPlanStorageResult(
            storage_kind="supabase",
            path=storage_key,
            bucket=bucket,
            public_url=public_url,
        )

    # Fallback: almacenamiento local usando default_storage
    content = ContentFile(uploaded_bytes)
    saved_path = default_storage.save(storage_key, content)
    try:
        public_url = default_storage.url(saved_path)
    except Exception:  # pragma: no cover - storage backend sin URL
        public_url = None

    return NutritionPlanStorageResult(
        storage_kind="local",
        path=saved_path,
        bucket=None,
        public_url=public_url,
    )


def enqueue_nutrition_plan_ingestion(
    *,
    job_id: uuid.UUID,
    auth_user_id: str,
    storage_result: NutritionPlanStorageResult,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Envía el trabajo de ingestión al servicio vectorial."""

    vector_url = getattr(settings, "NUTRITION_PLAN_INGESTION_URL", None)
    if not vector_url:
        raise NutritionPlanIngestionError("NUTRITION_PLAN_INGESTION_URL no está configurado.")

    ingestion_timeout = getattr(settings, "NUTRITION_PLAN_INGESTION_TIMEOUT", 30)
    ingestion_token = getattr(settings, "NUTRITION_PLAN_INGESTION_TOKEN", None)
    callback_url = getattr(settings, "NUTRITION_PLAN_CALLBACK_URL", None)
    callback_token = getattr(settings, "NUTRITION_PLAN_CALLBACK_TOKEN", None)

    payload: dict[str, Any] = {
        "job_id": str(job_id),
        "auth_user_id": auth_user_id,
        "source": {
            "kind": storage_result.storage_kind,
            "path": storage_result.path,
            "bucket": storage_result.bucket,
            "public_url": storage_result.public_url,
        },
        "metadata": metadata or {},
        "callback": {
            "url": callback_url,
            "token": callback_token,
        },
    }

    headers = {"Content-Type": "application/json"}
    if ingestion_token:
        headers["Authorization"] = f"Bearer {ingestion_token}"

    try:
        response = requests.post(
            vector_url,
            json=payload,
            headers=headers,
            timeout=ingestion_timeout,
        )
        response.raise_for_status()
        response_payload = response.json() if response.content else {}
    except RequestException as exc:
        logger.error(
            "Fallo al despachar ingestión de plan nutricional.",
            extra={
                "job_id": str(job_id),
                "vector_url": vector_url,
                "storage_path": storage_result.path,
            },
            exc_info=exc,
        )
        raise NutritionPlanIngestionError("El servicio vectorial rechazó la ingestión.") from exc
    except ValueError as exc:  # pragma: no cover - respuesta sin JSON
        logger.warning(
            "Respuesta sin JSON del servicio vectorial.",
            extra={"job_id": str(job_id), "vector_url": vector_url},
        )
        response_payload = {}

    return {"payload": response_payload, "request": payload}


def build_metadata_from_request(data: dict[str, Any]) -> dict[str, Any]:
    """Extrae campos relevantes del request para el servicio de ingestión."""

    optional_fields: Iterable[str] = (
        "title",
        "language",
        "issued_at",
        "valid_until",
        "notes",
    )
    metadata = {key: data[key] for key in optional_fields if data.get(key)}
    return metadata







