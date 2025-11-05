from __future__ import annotations

import time
from celery import Celery
from celery.result import AsyncResult
from loguru import logger

from vectosvc.api.schemas import NutritionPlanIngestRequest
from vectosvc.config import settings
from vectosvc.core.dlq import dlq
from vectosvc.core.nutrition_plan import (
    NutritionPlanProcessingError,
    dispatch_callback,
    process_nutrition_plan,
)
from vectosvc.core.pipeline import ingest_one
from vectosvc.core.schemas import IngestJob, IngestJobStatus, IngestRequest


celery = Celery(
    __name__, broker=settings.broker_url, backend=settings.result_backend
)

# Configuración de reintentos para el worker
celery.conf.task_acks_late = True
celery.conf.task_reject_on_worker_lost = True


def enqueue_ingest(req_model: IngestRequest) -> str:
    payload = req_model.model_dump()
    task = ingest_task.delay(payload)
    return task.id


def enqueue_batch(requests: list[IngestRequest]) -> list[str]:
    job_ids: list[str] = []
    for req in requests:
        job_ids.append(enqueue_ingest(req))
    return job_ids


def enqueue_nutrition_plan(req_model: NutritionPlanIngestRequest) -> str:
    payload = req_model.model_dump()
    task = nutrition_plan_ingest_task.delay(payload)
    return task.id


def get_job_status(job_id: str) -> IngestJob:
    result: AsyncResult = celery.AsyncResult(job_id)
    status = result.status

    status_map = {
        "PENDING": IngestJobStatus.QUEUED,
        "RECEIVED": IngestJobStatus.PROCESSING,
        "STARTED": IngestJobStatus.PROCESSING,
        "RETRY": IngestJobStatus.PROCESSING,
        "SUCCESS": IngestJobStatus.COMPLETED,
        "FAILURE": IngestJobStatus.FAILED,
    }

    meta = result.info if isinstance(result.info, dict) else {}
    doc_id = meta.get("doc_id")
    chunks = meta.get("chunks")
    error = None
    if result.failed():
        error = str(result.info)

    return IngestJob(
        job_id=job_id,
        status=status_map.get(status, IngestJobStatus.QUEUED),
        doc_id=doc_id,
        processed_chunks=chunks,
        total_chunks=chunks,
        error=error,
    )


@celery.task(
    name="ingest_task",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minuto entre reintentos
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # Máximo 10 minutos de backoff
    retry_jitter=True,
)
def ingest_task(self, req_dict):
    """
    Tarea de ingesta con reintentos automáticos y DLQ.
    
    - Reintentos: 3 con backoff exponencial + jitter
    - Si falla después de 3 reintentos, se envía al DLQ
    - Tracking completo de estado en Redis
    """
    doc_id = req_dict.get("doc_id")
    job_id = self.request.id
    attempt = self.request.retries + 1
    first_attempt_at = getattr(self.request, '_first_attempt_at', None)
    
    if first_attempt_at is None:
        first_attempt_at = int(time.time())
        self.request._first_attempt_at = first_attempt_at
    
    logger.info(
        "Starting ingest task doc_id={} job_id={} attempt={}/{}",
        doc_id,
        job_id,
        attempt,
        self.max_retries + 1
    )
    
    self.update_state(
        state="STARTED",
        meta={"doc_id": doc_id, "attempt": attempt}
    )
    
    try:
        chunk_count = ingest_one(req_dict)
        logger.info(
            "Ingest successful doc_id={} chunks={} attempt={}",
            doc_id,
            chunk_count,
            attempt
        )
        return {"status": "ok", "doc_id": doc_id, "chunks": chunk_count}
    
    except Exception as exc:
        # Si no quedan más reintentos, enviar al DLQ
        if attempt >= self.max_retries + 1:
            logger.error(
                "Ingest failed after {} attempts, sending to DLQ: doc_id={} error={}",
                attempt,
                doc_id,
                exc
            )
            
            # Determinar fase del error (básico)
            error_phase = "unknown"
            error_str = str(exc).lower()
            if "download" in error_str or "fetch" in error_str:
                error_phase = "download"
            elif "grobid" in error_str or "tei" in error_str or "parse" in error_str:
                error_phase = "parse_tei"
            elif "embed" in error_str or "encode" in error_str:
                error_phase = "embeddings"
            elif "upsert" in error_str or "qdrant" in error_str:
                error_phase = "upsert"
            
            # Push al DLQ
            try:
                dlq.push(
                    job_id=job_id,
                    doc_id=doc_id,
                    request=req_dict,
                    error=exc,
                    attempts=attempt,
                    error_phase=error_phase,
                    first_attempt_at=first_attempt_at,
                )
            except Exception as dlq_error:
                logger.error("Failed to push to DLQ: {}", dlq_error)
            
            # Re-raise para marcar como FAILURE en Celery
            raise
        
        else:
            # Aún hay reintentos disponibles
            logger.warning(
                "Ingest failed, will retry: doc_id={} attempt={}/{} error={}",
                doc_id,
                attempt,
                self.max_retries + 1,
                exc
            )
            # Re-raise para trigger automático de retry
            raise


def _push_to_dlq(
    job_id: str,
    req_dict: dict,
    error: Exception,
    attempt: int,
    first_attempt_at: int,
    phase: str,
) -> None:
    try:
        dlq.push(
            job_id=job_id,
            doc_id=req_dict.get("job_id", job_id),
            request=req_dict,
            error=error,
            attempts=attempt,
            error_phase=phase,
            first_attempt_at=first_attempt_at,
        )
    except Exception as dlq_error:  # pragma: no cover - logging defensivo
        logger.error("Failed to push nutrition plan job to DLQ: {}", dlq_error)


@celery.task(
    name="nutrition_plan_ingest_task",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    autoretry_for=(NutritionPlanProcessingError,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def nutrition_plan_ingest_task(self, req_dict):
    job_id = req_dict.get("job_id")
    attempt = self.request.retries + 1
    first_attempt_at = getattr(self.request, "_first_attempt_at", None)
    if first_attempt_at is None:
        first_attempt_at = int(time.time())
        self.request._first_attempt_at = first_attempt_at

    logger.info(
        "Starting nutrition plan ingest job_id={} celery_id={} attempt={}/{}",
        job_id,
        self.request.id,
        attempt,
        self.max_retries + 1,
    )

    self.update_state(state="STARTED", meta={"job_id": job_id, "attempt": attempt})

    try:
        req = NutritionPlanIngestRequest.model_validate(req_dict)
        result = process_nutrition_plan(req)
        dispatch_callback(req.callback, result)
        logger.info(
            "Nutrition plan ingest completed job_id={} plan_title={}",
            job_id,
            result.get("title"),
        )
        return {
            "status": "ok",
            "job_id": job_id,
            "plan_title": result.get("title"),
        }
    except NutritionPlanProcessingError as exc:
        logger.warning(
            "Nutrition plan ingest failed phase={} job_id={} attempt={}/{} error={}",
            exc.phase,
            job_id,
            attempt,
            self.max_retries + 1,
            exc.message,
        )
        if attempt >= self.max_retries + 1:
            _push_to_dlq(job_id, req_dict, exc, attempt, first_attempt_at, exc.phase)
        raise
    except Exception as exc:  # pragma: no cover - fallbacks generales
        logger.exception(
            "Unexpected error in nutrition plan ingest job_id={} attempt={}",
            job_id,
            attempt,
        )
        if attempt >= self.max_retries + 1:
            _push_to_dlq(job_id, req_dict, exc, attempt, first_attempt_at, "unknown")
        raise
