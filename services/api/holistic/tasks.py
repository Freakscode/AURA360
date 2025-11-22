"""Celery tasks para generación de snapshots y procesamiento del intake."""

from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

__all__ = [
    "generate_user_context_snapshots_periodic",
    "generate_user_context_snapshot_for_user",
    "vectorize_pending_snapshots",
    "process_intake_submission",
]


def _mark_submission_failed(submission, stage: str, reason: str):
    """Actualizar el estado del intake cuando ocurre un fallo."""

    from holistic.models import IntakeSubmissionStatus

    submission.status = IntakeSubmissionStatus.FAILED
    submission.processing_stage = stage
    submission.failure_reason = reason[:500]
    submission.last_error_at = timezone.now()
    submission.save(
        update_fields=[
            "status",
            "processing_stage",
            "failure_reason",
            "last_error_at",
            "updated_at",
        ]
    )
    logger.error("IntakeSubmission %s marcado como failed: %s", submission.id, reason)
    return {"status": "failed", "reason": reason}


def _build_intake_payload(submission):
    return {
        "submission_id": str(submission.id),
        "trace_id": str(submission.trace_id),
        "answers": submission.answers,
        "free_text": submission.free_text,
        "submitted_at": submission.created_at.isoformat() if submission.created_at else None,
    }


@shared_task(name="holistic.generate_user_context_snapshots_periodic")
def generate_user_context_snapshots_periodic():
    """Task periódico para generar snapshots de todos los usuarios activos.

    Se ejecuta cada 24 horas (configurado en Celery Beat).
    Genera snapshots mind + body para usuarios con actividad en últimos 7 días.
    """
    from body.models import BodyActivity, NutritionLog, SleepLog
    from holistic.context_aggregator import UserContextAggregator
    from holistic.context_vectorizer import UserContextVectorizer
    from holistic.models import UserContextSnapshot
    from users.models import AppUser

    # Usuarios con actividad en últimos 7 días
    cutoff = timezone.now() - timedelta(days=7)

    active_user_ids = set()

    # Usuarios con body activities
    try:
        body_active = BodyActivity.objects.filter(
            created_at__gte=cutoff
        ).values_list("auth_user_id", flat=True).distinct()
        active_user_ids.update(body_active)
    except Exception as exc:
        logger.warning(f"Error querying body activities: {exc}")

    # Usuarios con nutrition logs
    try:
        nutrition_active = NutritionLog.objects.filter(
            created_at__gte=cutoff
        ).values_list("auth_user_id", flat=True).distinct()
        active_user_ids.update(nutrition_active)
    except Exception as exc:
        logger.warning(f"Error querying nutrition logs: {exc}")

    # Usuarios con sleep logs
    try:
        sleep_active = SleepLog.objects.filter(
            created_at__gte=cutoff
        ).values_list("auth_user_id", flat=True).distinct()
        active_user_ids.update(sleep_active)
    except Exception as exc:
        logger.warning(f"Error querying sleep logs: {exc}")

    logger.info(f"Found {len(active_user_ids)} active users for snapshot generation")

    if not active_user_ids:
        logger.info("No active users, skipping snapshot generation")
        return {"status": "skipped", "reason": "no_active_users"}

    aggregator = UserContextAggregator()
    vectorizer = UserContextVectorizer()

    snapshots_created = 0
    snapshots_updated = 0
    errors = []

    for user_id in active_user_ids:
        user_id_str = str(user_id)

        # Generar snapshot mind (7d)
        try:
            mind_context = aggregator.aggregate_mind_context(user_id_str, "7d")

            snapshot, created = UserContextSnapshot.objects.update_or_create(
                auth_user_id=user_id,
                snapshot_type="mind",
                timeframe="7d",
                defaults={
                    "consolidated_text": mind_context["text"],
                    "metadata": mind_context["metadata"],
                    "is_active": True,
                },
            )

            if created:
                snapshots_created += 1
            else:
                snapshots_updated += 1

            # Vectorizar si es nuevo o no ha sido vectorizado
            if created or not snapshot.vectorized_at:
                try:
                    vectorizer.vectorize_snapshot(snapshot)
                except Exception as vec_exc:
                    logger.error(
                        f"Failed to vectorize mind snapshot for user {user_id}: {vec_exc}"
                    )
                    errors.append(
                        {
                            "user_id": user_id_str,
                            "snapshot_type": "mind",
                            "error": str(vec_exc),
                        }
                    )

        except Exception as exc:
            logger.error(f"Failed to generate mind snapshot for user {user_id}: {exc}")
            errors.append(
                {
                    "user_id": user_id_str,
                    "snapshot_type": "mind",
                    "error": str(exc),
                }
            )

        # Generar snapshot body (7d)
        try:
            body_context = aggregator.aggregate_body_context(user_id_str, "7d")

            snapshot, created = UserContextSnapshot.objects.update_or_create(
                auth_user_id=user_id,
                snapshot_type="body",
                timeframe="7d",
                defaults={
                    "consolidated_text": body_context["text"],
                    "metadata": body_context["metadata"],
                    "is_active": True,
                },
            )

            if created:
                snapshots_created += 1
            else:
                snapshots_updated += 1

            # Vectorizar si es nuevo o no ha sido vectorizado
            if created or not snapshot.vectorized_at:
                try:
                    vectorizer.vectorize_snapshot(snapshot)
                except Exception as vec_exc:
                    logger.error(
                        f"Failed to vectorize body snapshot for user {user_id}: {vec_exc}"
                    )
                    errors.append(
                        {
                            "user_id": user_id_str,
                            "snapshot_type": "body",
                            "error": str(vec_exc),
                        }
                    )

        except Exception as exc:
            logger.error(f"Failed to generate body snapshot for user {user_id}: {exc}")
            errors.append(
                {
                    "user_id": user_id_str,
                    "snapshot_type": "body",
                    "error": str(exc),
                }
            )

    logger.info(
        f"Snapshot generation complete: {snapshots_created} created, "
        f"{snapshots_updated} updated, {len(errors)} errors"
    )

    return {
        "status": "completed",
        "snapshots_created": snapshots_created,
        "snapshots_updated": snapshots_updated,
        "users_processed": len(active_user_ids),
        "errors": errors,
    }


@shared_task(name="holistic.generate_user_context_snapshot_for_user")
def generate_user_context_snapshot_for_user(
    user_id: str,
    snapshot_type: str,
    timeframe: str = "7d",
    vectorize: bool = True,
):
    """Task event-driven para generar snapshot de un usuario específico.

    Args:
        user_id: UUID del usuario
        snapshot_type: Tipo de snapshot ("mind", "body", "soul", "holistic")
        timeframe: Ventana temporal ("7d", "30d", "90d")
        vectorize: Si debe vectorizar inmediatamente

    Returns:
        Dict con status y detalles del snapshot
    """
    from holistic.context_aggregator import UserContextAggregator
    from holistic.context_vectorizer import UserContextVectorizer
    from holistic.models import UserContextSnapshot

    aggregator = UserContextAggregator()

    # Generar contexto según tipo
    try:
        if snapshot_type == "mind":
            context = aggregator.aggregate_mind_context(user_id, timeframe)
        elif snapshot_type == "body":
            context = aggregator.aggregate_body_context(user_id, timeframe)
        elif snapshot_type == "soul":
            context = aggregator.aggregate_soul_context(user_id)
        elif snapshot_type == "holistic":
            context = aggregator.aggregate_holistic_context(user_id, timeframe)
        else:
            raise ValueError(f"Invalid snapshot_type: {snapshot_type}")

    except Exception as exc:
        logger.error(
            f"Failed to aggregate {snapshot_type} context for user {user_id}: {exc}",
            exc_info=True,
        )
        return {
            "status": "error",
            "error": str(exc),
            "user_id": user_id,
            "snapshot_type": snapshot_type,
        }

    # Crear/actualizar snapshot
    try:
        snapshot, created = UserContextSnapshot.objects.update_or_create(
            auth_user_id=user_id,
            snapshot_type=snapshot_type,
            timeframe=timeframe,
            defaults={
                "consolidated_text": context["text"],
                "metadata": context["metadata"],
                "is_active": True,
            },
        )

        logger.info(
            f"{'Created' if created else 'Updated'} {snapshot_type} snapshot "
            f"for user {user_id} (snapshot_id={snapshot.id})"
        )

    except Exception as exc:
        logger.error(
            f"Failed to save {snapshot_type} snapshot for user {user_id}: {exc}",
            exc_info=True,
        )
        return {
            "status": "error",
            "error": str(exc),
            "user_id": user_id,
            "snapshot_type": snapshot_type,
        }

    # Vectorizar si se solicita
    if vectorize:
        try:
            vectorizer = UserContextVectorizer()
            vectorizer.vectorize_snapshot(snapshot)

            return {
                "status": "success",
                "snapshot_id": str(snapshot.id),
                "created": created,
                "vectorized": True,
                "user_id": user_id,
                "snapshot_type": snapshot_type,
            }

        except Exception as exc:
            logger.error(
                f"Failed to vectorize {snapshot_type} snapshot "
                f"for user {user_id}: {exc}",
                exc_info=True,
            )
            return {
                "status": "partial_success",
                "snapshot_id": str(snapshot.id),
                "created": created,
                "vectorized": False,
                "vectorization_error": str(exc),
                "user_id": user_id,
                "snapshot_type": snapshot_type,
            }

    return {
        "status": "success",
        "snapshot_id": str(snapshot.id),
        "created": created,
        "vectorized": False,
        "user_id": user_id,
        "snapshot_type": snapshot_type,
    }


@shared_task(name="holistic.vectorize_pending_snapshots")
def vectorize_pending_snapshots(limit: int = 100):
    """Task para vectorizar snapshots que aún no han sido vectorizados.

    Útil para recuperar de fallos de vectorización.

    Args:
        limit: Máximo número de snapshots a procesar

    Returns:
        Dict con status y estadísticas
    """
    from holistic.context_vectorizer import UserContextVectorizer
    from holistic.models import UserContextSnapshot

    # Buscar snapshots activos sin vectorizar
    pending = UserContextSnapshot.objects.filter(
        is_active=True, vectorized_at__isnull=True
    ).order_by("created_at")[:limit]

    if not pending:
        logger.info("No pending snapshots to vectorize")
        return {"status": "completed", "processed": 0}

    vectorizer = UserContextVectorizer()
    succeeded = 0
    failed = 0
    errors = []

    for snapshot in pending:
        try:
            vectorizer.vectorize_snapshot(snapshot)
            succeeded += 1
        except Exception as exc:
            failed += 1
            errors.append(
                {"snapshot_id": str(snapshot.id), "error": str(exc)}
            )
            logger.error(
                f"Failed to vectorize snapshot {snapshot.id}: {exc}",
                exc_info=True,
            )

    logger.info(
        f"Vectorization complete: {succeeded} succeeded, {failed} failed"
    )

    return {
        "status": "completed",
        "processed": len(pending),
        "succeeded": succeeded,
        "failed": failed,
        "errors": errors,
    }


@shared_task(name="holistic.process_intake_submission")
def process_intake_submission(submission_id: str):
    """Orquesta la contextualización, llamada a agentes y generación de PDF."""

    from holistic.context_aggregator import UserContextAggregator
    from holistic.context_vectorizer import UserContextVectorizer
    from holistic.models import (
        HolisticAgentProfile,
        HolisticAgentRunStatus,
        HolisticCategory,
        HolisticRequest,
        HolisticRequestStatus,
        IntakeSubmission,
        IntakeSubmissionStatus,
        SnapshotType,
        TimeframeChoices,
        UserContextSnapshot,
    )
    from holistic.reporting import generate_personalized_report
    from holistic.services import (
        call_agent_service,
        create_agent_run,
        fetch_user_profile,
        persist_vector_queries,
    )

    try:
        with transaction.atomic():
            submission = (
                IntakeSubmission.objects.select_for_update()
                .get(id=submission_id)
            )
            if submission.status not in {
                IntakeSubmissionStatus.PENDING,
                IntakeSubmissionStatus.FAILED,
            }:
                logger.info(
                    "Skipping intake %s (status=%s)",
                    submission_id,
                    submission.status,
                )
                return {"status": "skipped", "current_status": submission.status}

            submission.status = IntakeSubmissionStatus.PROCESSING
            submission.processing_stage = "collected"
            submission.failure_reason = ""
            submission.last_error_at = None
            submission.save(
                update_fields=[
                    "status",
                    "processing_stage",
                    "failure_reason",
                    "last_error_at",
                    "updated_at",
                ]
            )
    except IntakeSubmission.DoesNotExist:
        logger.warning("IntakeSubmission %s no encontrado", submission_id)
        return {"status": "not_found"}

    auth_user_id = str(submission.auth_user_id)
    timeframe = TimeframeChoices.THIRTY_DAYS

    aggregator = UserContextAggregator()
    try:
        holistic_context = aggregator.aggregate_holistic_context(auth_user_id, timeframe)
    except Exception as exc:  # pragma: no cover - relies on aggregator implementation
        return _mark_submission_failed(submission, "aggregation", f"aggregation_error: {exc}")

    submission.processing_stage = "contextualized"
    submission.save(update_fields=["processing_stage", "updated_at"])

    snapshot_metadata = dict(holistic_context.get("metadata", {}))
    snapshot_metadata["intake_answers"] = submission.answers
    snapshot_metadata["intake_free_text"] = submission.free_text

    snapshot, _ = UserContextSnapshot.objects.update_or_create(
        auth_user_id=submission.auth_user_id,
        snapshot_type=SnapshotType.HOLISTIC,
        timeframe=timeframe,
        defaults={
            "consolidated_text": holistic_context.get("text", ""),
            "metadata": snapshot_metadata,
            "is_active": True,
        },
    )

    if submission.vectorize_snapshot:
        try:
            vectorizer = UserContextVectorizer()
            vectorizer.vectorize_snapshot(snapshot)
        except Exception as exc:  # pragma: no cover - Qdrant interaction
            logger.warning(
                "Fallo vectorizando snapshot %s: %s",
                snapshot.id,
                exc,
            )

    agent_profile = (
        HolisticAgentProfile.objects.filter(
            category=HolisticCategory.HOLISTIC,
            is_active=True,
        )
        .order_by("-version")
        .first()
    )
    if agent_profile is None:
        return _mark_submission_failed(
            submission,
            "agent_profile",
            "agent_profile_not_found",
        )

    try:
        user_profile = fetch_user_profile(auth_user_id)
    except Exception as exc:  # pragma: no cover - Supabase dependency
        return _mark_submission_failed(submission, "profile", f"profile_error: {exc}")

    intake_payload = _build_intake_payload(submission)
    agent_payload = {
        "trace_id": str(submission.trace_id),
        "user": user_profile,
        "category": HolisticCategory.HOLISTIC,
        "metadata": {
            "source": "intake_submission",
            "intake_submission_id": intake_payload["submission_id"],
        },
        "request_context": {
            "snapshot_id": str(snapshot.id),
            "timeframe": timeframe,
            "intake": intake_payload,
            "holistic_context": holistic_context,
        },
        "agent_profile": {
            "primary_agent": agent_profile.primary_agent,
            "fallback_agents": agent_profile.fallback_agents,
            "embedding_model": agent_profile.embedding_model,
            "prompt_template": agent_profile.prompt_template,
            "version": agent_profile.version,
        },
    }

    submission.processing_stage = "recommendations"
    submission.save(update_fields=["processing_stage", "updated_at"])

    timeout = getattr(settings, "HOLISTIC_AGENT_REQUEST_TIMEOUT", 120)
    agent_response = call_agent_service(agent_payload, str(submission.trace_id), timeout=timeout)

    agent_status = agent_response.get("status")
    agent_data = agent_response.get("data")
    agent_error = agent_response.get("error")
    latency_ms = agent_response.get("latency_ms")

    request_defaults = {
        "user_id": auth_user_id,
        "category": HolisticCategory.HOLISTIC,
        "status": HolisticRequestStatus.PENDING,
        "request_payload": agent_payload,
    }
    holistic_request, _ = HolisticRequest.objects.get_or_create(
        trace_id=submission.trace_id,
        defaults=request_defaults,
    )

    run_status = (
        HolisticAgentRunStatus.COMPLETED
        if agent_status == "success"
        else HolisticAgentRunStatus.FAILED
    )

    with transaction.atomic():
        agent_run = create_agent_run(
            holistic_request,
            agent_name=agent_profile.primary_agent,
            status=run_status,
            latency_ms=latency_ms,
            input_context=agent_payload,
            output_payload=agent_data if agent_status == "success" else agent_error or {},
            error_type=(agent_error or {}).get("type") if agent_error else None,
        )

        if agent_status == "success":
            holistic_request.status = HolisticRequestStatus.COMPLETED
            holistic_request.response_payload = agent_data
            holistic_request.error_type = None
            holistic_request.save(
                update_fields=["status", "response_payload", "error_type", "updated_at"]
            )
            vector_queries = (agent_data or {}).get("vector_queries") if isinstance(agent_data, dict) else None
            if vector_queries:
                persist_vector_queries(agent_run, vector_queries)
        else:
            holistic_request.status = HolisticRequestStatus.FAILED
            holistic_request.response_payload = agent_data
            holistic_request.error_type = (agent_error or {}).get("type") or "unknown_error"
            holistic_request.save(
                update_fields=["status", "response_payload", "error_type", "updated_at"]
            )

    if agent_status != "success":
        error_message = (agent_error or {}).get("message") or "agent_error"
        return _mark_submission_failed(
            submission,
            "agent_execution",
            error_message,
        )

    submission.processing_stage = "report_generation"
    submission.save(update_fields=["processing_stage", "updated_at"])

    report_payload = {
        "trace_id": str(submission.trace_id),
        "participant": user_profile,
        "intake": intake_payload,
        "agent_output": agent_data,
        "snapshot": {
            "id": str(snapshot.id),
            "timeframe": timeframe,
            "consolidated_text": snapshot.consolidated_text,
            "metadata": snapshot.metadata,
        },
    }

    report_response = generate_personalized_report(report_payload)
    submission.status = IntakeSubmissionStatus.READY
    submission.processing_stage = "report_ready"
    submission.report_url = (report_response or {}).get("url")
    submission.report_storage_path = (report_response or {}).get("storage_path", "")
    submission.report_metadata = (report_response or {}).get("metadata", {})
    submission.save(
        update_fields=[
            "status",
            "processing_stage",
            "report_url",
            "report_storage_path",
            "report_metadata",
            "updated_at",
        ]
    )

    return {
        "status": "completed",
        "submission_id": submission_id,
        "report_url": submission.report_url,
    }
