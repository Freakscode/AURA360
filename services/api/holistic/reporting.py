"""Helper para generación de reportes PDF personalizados."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_personalized_report(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Invoca el microservicio (o stub) encargado de renderizar el PDF.

    Devuelve un diccionario con las llaves `url`, `storage_path` y `metadata` cuando
    la generación fue exitosa. Si la integración no está configurada o falla, retorna
    ``None`` para que el caller maneje la ausencia del reporte.
    """

    service_url = getattr(settings, "HOLISTIC_REPORT_SERVICE_URL", None)
    if not service_url:
        logger.warning("HOLISTIC_REPORT_SERVICE_URL no configurado; omitiendo PDF.")
        return None

    timeout = getattr(settings, "HOLISTIC_REPORT_SERVICE_TIMEOUT", 30)
    token = getattr(settings, "HOLISTIC_REPORT_SERVICE_TOKEN", None)

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.post(service_url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Respuesta inválida del servicio de reportes")
        return data
    except Exception as exc:  # pragma: no cover - logging only
        logger.error("Fallo al generar el reporte personalizado: %s", exc, exc_info=True)
        return None
