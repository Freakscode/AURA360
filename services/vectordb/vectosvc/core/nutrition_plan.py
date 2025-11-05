"""Pipeline para extraer y estructurar planes nutricionales desde PDFs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import httpx
from loguru import logger

from vectosvc.api.schemas import NutritionPlanCallback, NutritionPlanIngestRequest, NutritionPlanSource
from vectosvc.config import settings
from vectosvc.core.parsers.pdf import extract_plain_text


class NutritionPlanProcessingError(Exception):
    """Error controlado dentro del pipeline de ingestión."""

    def __init__(self, message: str, phase: str) -> None:
        super().__init__(message)
        self.message = message
        self.phase = phase


def process_nutrition_plan(request: NutritionPlanIngestRequest) -> dict[str, Any]:
    """Procesa el PDF y devuelve el payload estructurado listo para el backend."""

    logger.bind(job_id=request.job_id).info(
        "nutrition_plan.process.start", source_kind=request.source.kind
    )

    pdf_bytes = _download_pdf(request.source)
    raw_text = _extract_text(pdf_bytes, request)

    structured_plan, llm_meta = _generate_structured_plan(raw_text, request.metadata)
    payload = _assemble_payload(request, structured_plan, raw_text, llm_meta)

    logger.bind(job_id=request.job_id).info(
        "nutrition_plan.process.success",
        title=payload.get("title"),
        language=payload.get("language"),
    )

    return payload


def dispatch_callback(callback: NutritionPlanCallback | None, payload: dict[str, Any]) -> None:
    if callback is None:
        logger.debug("nutrition_plan.callback.skipped")
        return

    timeout = settings.nutrition_plan_callback_timeout
    headers = {"Content-Type": "application/json"}
    if callback.token:
        headers["Authorization"] = f"Bearer {callback.token}"

    logger.bind(url=str(callback.url)).info("nutrition_plan.callback.dispatch")

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(str(callback.url), json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # pragma: no cover - depende de red
        raise NutritionPlanProcessingError(
            f"Callback HTTP {exc.response.status_code}", phase="callback"
        ) from exc
    except httpx.RequestError as exc:  # pragma: no cover - depende de red
        raise NutritionPlanProcessingError(
            "No se pudo contactar el callback del backend.", phase="callback"
        ) from exc


def _download_pdf(source: NutritionPlanSource) -> bytes:
    if source.public_url:
        return _fetch_http_bytes(str(source.public_url))

    if source.kind in {"http", "https"}:
        url = source.path if source.path.startswith("http") else f"{source.kind}://{source.path}"
        return _fetch_http_bytes(url)

    if source.kind == "supabase":
        if not source.bucket:
            raise NutritionPlanProcessingError(
                "Se requiere bucket para leer desde Supabase Storage.", phase="download"
            )
        if not settings.supabase_api_url or not settings.supabase_service_role_key:
            raise NutritionPlanProcessingError(
                "Configura SUPABASE_API_URL y SUPABASE_SERVICE_ROLE_KEY en el servicio vectorial.",
                phase="download",
            )
        endpoint = (
            f"{settings.supabase_api_url.rstrip('/')}/storage/v1/object/"
            f"{source.bucket}/{source.path.lstrip('/')}"
        )
        headers = {
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Accept": "application/octet-stream",
        }
        return _fetch_http_bytes(endpoint, headers=headers)

    if source.kind == "local":
        path = Path(source.path)
        if not path.exists():
            raise NutritionPlanProcessingError(
                f"Archivo local no encontrado en {path}.", phase="download"
            )
        try:
            return path.read_bytes()
        except OSError as exc:
            raise NutritionPlanProcessingError(
                f"No se pudo leer el archivo local: {exc}", phase="download"
            ) from exc

    raise NutritionPlanProcessingError(
        f"Origen de archivo no soportado: {source.kind}", phase="download"
    )


def _fetch_http_bytes(url: str, headers: dict[str, str] | None = None) -> bytes:
    timeout = settings.nutrition_plan_download_timeout
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return response.content
    except httpx.HTTPStatusError as exc:
        raise NutritionPlanProcessingError(
            f"HTTP {exc.response.status_code} al descargar el PDF.", phase="download"
        ) from exc
    except httpx.RequestError as exc:
        raise NutritionPlanProcessingError(
            "No se pudo descargar el PDF desde la fuente remota.", phase="download"
        ) from exc


def _extract_text(pdf_bytes: bytes, request: NutritionPlanIngestRequest) -> str:
    try:
        parsed = extract_plain_text(pdf_bytes, doc_id=request.job_id, source=request.source.path)
    except Exception as exc:  # pragma: no cover - fallback depende de libs
        raise NutritionPlanProcessingError(
            "No se pudo extraer texto del PDF.", phase="parse"
        ) from exc

    segments = [segment.text.strip() for segment in parsed.segments if segment.text.strip()]
    combined = "\n\n".join(segments)
    if not combined:
        raise NutritionPlanProcessingError(
            "El PDF no contiene texto legible luego de la extracción.", phase="parse"
        )
    return combined


def _generate_structured_plan(text: str, metadata: dict[str, Any]) -> Tuple[dict[str, Any], dict[str, Any]]:
    trimmed = text[: settings.nutrition_plan_prompt_max_chars]
    messages = _build_prompt(trimmed, metadata)
    content, usage = _invoke_llm(messages)
    plan_dict = _extract_json_payload(content)
    return plan_dict, {
        "raw_response": content[: settings.nutrition_plan_llm_response_excerpt],
        "usage": usage,
        "prompt_chars": len(trimmed),
    }


def _build_prompt(text: str, metadata: dict[str, Any]) -> list[dict[str, str]]:
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False, indent=2)
    template_description = (
        "Debes devolver un JSON con esta forma base:\n"
        "{\n"
        "  \"title\": string,\n"
        "  \"language\": string,\n"
        "  \"issued_at\": string | null,\n"
        "  \"valid_until\": string | null,\n"
        "  \"is_active\": boolean,\n"
        "  \"plan_data\": {\n"
        "    \"plan\": {...},\n"
        "    \"subject\": {...},\n"
        "    \"assessment\": {...},\n"
        "    \"directives\": {...},\n"
        "    \"supplements\": [...],\n"
        "    \"recommendations\": [...]\n"
        "  }\n"
        "}\n"
    )
    system_content = (
        "Eres un analista nutricional experto. Lee un plan nutricional en texto plano y "
        "reescribe su contenido en un JSON estructurado que siga la plantilla de planes "
        "nutricionales de AURA360. Respeta las unidades y reproduce tablas y horarios en forma de listas."
    )
    user_content = (
        f"Metadatos iniciales:\n{metadata_json}\n\n"
        f"Texto del plan:\n{text}\n\n"
        f"{template_description}\n"
        "Responde únicamente con JSON válido sin comentarios ni explicaciones adicionales."
    )
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def _invoke_llm(messages: list[dict[str, str]]) -> Tuple[str, dict[str, Any] | None]:
    if not settings.deepseek_api_url:
        raise NutritionPlanProcessingError(
            "DEEPSEEK_API_URL no configurado para el servicio vectorial.", phase="llm"
        )

    payload: dict[str, Any] = {
        "model": settings.nutrition_plan_llm_model,
        "messages": messages,
        "temperature": settings.nutrition_plan_llm_temperature,
        "max_tokens": settings.nutrition_plan_llm_max_output_tokens,
    }

    headers = {"Content-Type": "application/json"}
    if settings.deepseek_api_key:
        headers["Authorization"] = f"Bearer {settings.deepseek_api_key}"

    try:
        with httpx.Client(timeout=settings.deepseek_timeout) as client:
            response = client.post(settings.deepseek_api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        raise NutritionPlanProcessingError(
            f"El modelo devolvió HTTP {exc.response.status_code}.", phase="llm"
        ) from exc
    except httpx.RequestError as exc:
        raise NutritionPlanProcessingError(
            "Error de red al invocar el modelo DeepSeek.", phase="llm"
        ) from exc
    except ValueError as exc:  # pragma: no cover - dependerá de respuesta inválida
        raise NutritionPlanProcessingError(
            "La respuesta del modelo no es JSON válido.", phase="llm"
        ) from exc

    choices = data.get("choices") or []
    if not choices:
        raise NutritionPlanProcessingError(
            "El modelo no devolvió ninguna opción.", phase="llm"
        )

    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise NutritionPlanProcessingError(
            "El modelo no devolvió contenido en el mensaje.", phase="llm"
        )

    usage = data.get("usage")
    return str(content), usage


def _extract_json_payload(content: str) -> dict[str, Any]:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        raise NutritionPlanProcessingError(
            "La respuesta del modelo no contiene JSON.", phase="llm"
        )

    snippet = content[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise NutritionPlanProcessingError(
            "No se pudo parsear el JSON devuelto por el modelo.", phase="llm"
        ) from exc


def _assemble_payload(
    request: NutritionPlanIngestRequest,
    plan_dict: dict[str, Any],
    raw_text: str,
    llm_meta: dict[str, Any],
) -> dict[str, Any]:
    metadata = request.metadata or {}
    plan_data = plan_dict.get("plan_data") or plan_dict

    title = plan_dict.get("title") or metadata.get("title") or "Plan nutricional generado"
    language = plan_dict.get("language") or metadata.get("language") or "es"
    issued_at = plan_dict.get("issued_at") or metadata.get("issued_at")
    valid_until = plan_dict.get("valid_until") or metadata.get("valid_until")
    is_active = bool(plan_dict.get("is_active", True))

    extractor_info = {
        "name": "deepseek-7b",
        "model": settings.nutrition_plan_llm_model,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    plan_section = plan_data.setdefault("plan", {}) if isinstance(plan_data, dict) else {}
    if isinstance(plan_section, dict):
        plan_section.setdefault("title", title)
        plan_section.setdefault("language", language)
        plan_section.setdefault("issued_at", issued_at)
        plan_section.setdefault("valid_until", valid_until)

        plan_source = plan_section.setdefault("source", {})
        if not isinstance(plan_source, dict):
            plan_source = {}
            plan_section["source"] = plan_source
        plan_source.setdefault("kind", "pdf")
        plan_source.setdefault("storage_kind", request.source.kind)
        plan_source.setdefault("path", request.source.path)
        plan_source.setdefault("bucket", request.source.bucket)
        plan_source.setdefault(
            "public_url",
            str(request.source.public_url) if request.source.public_url else None,
        )
        plan_source.setdefault("job_id", request.job_id)

        plan_section.setdefault("extractor", extractor_info["name"])
        plan_section.setdefault("extracted_at", extractor_info["extracted_at"])

    payload = {
        "job_id": request.job_id,
        "auth_user_id": request.auth_user_id,
        "title": title,
        "language": language,
        "issued_at": issued_at,
        "valid_until": valid_until,
        "is_active": is_active,
        "plan_data": plan_data,
        "metadata": metadata,
        "source": {
            "kind": "pdf",
            "storage_kind": request.source.kind,
            "path": request.source.path,
            "bucket": request.source.bucket,
            "public_url": str(request.source.public_url) if request.source.public_url else None,
        },
        "extractor": extractor_info,
        "raw_text_excerpt": raw_text[: settings.nutrition_plan_text_excerpt],
        "llm": llm_meta,
    }

    return payload


