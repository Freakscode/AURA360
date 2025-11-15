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


# ============================================================================
# KAFKA EVENT FALLBACK TASKS
# ============================================================================
# These tasks provide Celery fallback when Kafka is unavailable
# They mirror the logic in vectosvc.kafka.consumer
# ============================================================================

@celery.task(
    name="vectosvc.worker.tasks.process_mood_created",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_mood_created(self, event_dict: dict):
    """
    Celery fallback for user.mood.created event.

    Mirrors logic from vectosvc.kafka.consumer.handle_mood_created.

    Args:
        event_dict: Serialized MoodCreatedEvent
    """
    from vectosvc.kafka.consumer import aggregate_user_context

    user_id = event_dict.get("user_id")
    event_data = event_dict.get("data", {})
    event_type = event_dict.get("event_type", "user.mood.created")

    logger.info("Processing mood event (Celery fallback): user_id={}", user_id)

    try:
        # Aggregate context
        context_data = aggregate_user_context(
            user_id=user_id,
            event_data=event_data,
            event_type=event_type,
        )

        # Trigger vectorization (chain to next task)
        process_context_aggregated.delay({
            "user_id": user_id,
            "trace_id": event_dict.get("trace_id"),
            "context_data": context_data,
        })

        logger.info("Context aggregated (Celery): user_id={}", user_id)
        return {"status": "ok", "user_id": user_id}

    except Exception as exc:
        logger.error("Failed to process mood event (Celery): user_id={} error={}", user_id, exc)
        raise


@celery.task(
    name="vectosvc.worker.tasks.process_activity_created",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_activity_created(self, event_dict: dict):
    """
    Celery fallback for user.activity.created event.

    Mirrors logic from vectosvc.kafka.consumer.handle_activity_created.

    Args:
        event_dict: Serialized ActivityCreatedEvent
    """
    from vectosvc.kafka.consumer import aggregate_user_context

    user_id = event_dict.get("user_id")
    event_data = event_dict.get("data", {})
    event_type = event_dict.get("event_type", "user.activity.created")

    logger.info("Processing activity event (Celery fallback): user_id={}", user_id)

    try:
        # Aggregate context
        context_data = aggregate_user_context(
            user_id=user_id,
            event_data=event_data,
            event_type=event_type,
        )

        # Trigger vectorization (chain to next task)
        process_context_aggregated.delay({
            "user_id": user_id,
            "trace_id": event_dict.get("trace_id"),
            "context_data": context_data,
        })

        logger.info("Context aggregated (Celery): user_id={}", user_id)
        return {"status": "ok", "user_id": user_id}

    except Exception as exc:
        logger.error("Failed to process activity event (Celery): user_id={} error={}", user_id, exc)
        raise


@celery.task(
    name="vectosvc.worker.tasks.process_context_aggregated",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_context_aggregated(self, event_dict: dict):
    """
    Celery fallback for context.aggregated event.

    Mirrors logic from vectosvc.kafka.consumer.handle_context_aggregated.

    Args:
        event_dict: Serialized ContextAggregatedEvent
    """
    from vectosvc.kafka.consumer import vectorize_context

    user_id = event_dict.get("user_id")
    context_data = event_dict.get("context_data", {})
    trace_id = event_dict.get("trace_id")

    logger.info("Processing context aggregation (Celery fallback): user_id={}", user_id)

    try:
        # Vectorize and ingest
        result = vectorize_context(
            context_data=context_data,
            user_id=user_id,
            trace_id=trace_id,
        )

        if result["status"] == "completed":
            logger.info(
                "Context vectorized (Celery): user_id={} doc_id={} chunks={}",
                user_id,
                result["doc_id"],
                result["chunk_count"],
            )
            return {
                "status": "ok",
                "user_id": user_id,
                "doc_id": result["doc_id"],
                "chunks": result["chunk_count"],
            }
        else:
            logger.warning(
                "Context vectorization failed (Celery): user_id={} status={}",
                user_id,
                result["status"],
            )
            return {"status": "failed", "user_id": user_id, "reason": result.get("error")}

    except Exception as exc:
        logger.error("Failed to vectorize context (Celery): user_id={} error={}", user_id, exc)
        raise


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
