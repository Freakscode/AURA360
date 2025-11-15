"""
Kafka Consumer for Vectordb Service

Consumes events from Kafka topics and processes them through the existing pipeline:
- user.mood.created → aggregate context
- user.activity.created → aggregate context
- context.aggregated → vectorize and publish ContextVectorizedEvent

Orchestrates existing code from:
- vectosvc.core.pipeline (ingest_one)
- vectosvc.core.embeddings (Embeddings)
- vectosvc.core.qdrant_store (store, QdrantStore)
"""

import json
import signal
import sys
import time
from typing import Dict, Any
from loguru import logger

from messaging import EventHandler, EventPublisher
from messaging.events import (
    MoodCreatedEvent,
    ActivityCreatedEvent,
    ContextAggregatedEvent,
    ContextVectorizedEvent,
    EventType,
)

from vectosvc.config import settings, service_settings
from vectosvc.core.embeddings import Embeddings
from vectosvc.core.pipeline import ingest_one
from vectosvc.core.qdrant_store import store


# ============================================================================
# CONTEXT AGGREGATION (from user events)
# ============================================================================

def aggregate_user_context(user_id: str, event_data: Dict[str, Any], event_type: str) -> Dict[str, Any]:
    """
    Aggregate user context from individual events.

    This is a simplified aggregation. In production, you would:
    1. Fetch recent user data from Supabase/Django API
    2. Combine mood, activity, IKIGAI, psychosocial factors
    3. Create a comprehensive snapshot

    For now, we'll create a basic context payload that can be vectorized.

    Args:
        user_id: User identifier
        event_data: Data from the event
        event_type: Type of event (mood.created, activity.created, etc.)

    Returns:
        Context data ready for vectorization
    """
    # Build context snapshot
    context_snapshot = {
        "user_id": user_id,
        "snapshot_type": "incremental",
        "timeframe": "recent",
        "timestamp": int(time.time()),
        "source_event": event_type,
    }

    # Add event-specific data
    if event_type == "user.mood.created":
        context_snapshot["mood_summary"] = {
            "recent_score": event_data.get("mood_score"),
            "tags": event_data.get("tags", []),
            "notes": event_data.get("notes", ""),
        }
    elif event_type == "user.activity.created":
        context_snapshot["activity_summary"] = {
            "activity_type": event_data.get("activity_type"),
            "duration": event_data.get("duration"),
            "calories": event_data.get("calories"),
        }

    # Create a text representation for vectorization
    context_text = _build_context_text(context_snapshot)
    context_snapshot["text_representation"] = context_text

    return context_snapshot


def _build_context_text(context: Dict[str, Any]) -> str:
    """
    Build a natural language representation of user context.

    This text will be vectorized and stored in Qdrant for retrieval.
    """
    parts = []

    # User ID
    parts.append(f"User: {context.get('user_id')}")

    # Mood data
    if "mood_summary" in context:
        mood = context["mood_summary"]
        parts.append(f"Mood Score: {mood.get('recent_score')}/10")
        if mood.get("tags"):
            parts.append(f"Mood Tags: {', '.join(mood['tags'])}")
        if mood.get("notes"):
            parts.append(f"Notes: {mood['notes']}")

    # Activity data
    if "activity_summary" in context:
        activity = context["activity_summary"]
        parts.append(f"Activity: {activity.get('activity_type')}")
        parts.append(f"Duration: {activity.get('duration')} minutes")
        if activity.get("calories"):
            parts.append(f"Calories: {activity.get('calories')}")

    return " | ".join(parts)


# ============================================================================
# VECTORIZATION (from aggregated context)
# ============================================================================

def vectorize_context(context_data: Dict[str, Any], user_id: str, trace_id: str) -> Dict[str, Any]:
    """
    Vectorize aggregated context and ingest into Qdrant.

    Uses existing pipeline code:
    - Embeddings for vector generation
    - ingest_one for storing in Qdrant

    Args:
        context_data: Aggregated context data
        user_id: User identifier
        trace_id: Trace ID for distributed tracing

    Returns:
        Result with ingestion statistics
    """
    try:
        text_representation = context_data.get("text_representation", "")

        if not text_representation:
            logger.warning("No text representation in context_data, skipping vectorization")
            return {"status": "skipped", "reason": "no_text"}

        # Create IngestRequest payload for the existing pipeline
        # This will use source_type="user_context" to route to the correct collection
        ingest_payload = {
            "doc_id": f"user_context_{user_id}_{int(time.time())}",
            "text": text_representation,
            "category": "user_context",
            "locale": "en",
            "source_type": "user_context",  # Routes to "user_context" collection
            "chunk_size": 900,
            "chunk_overlap": 150,
            "metadata": {
                "user_id": user_id,
                "snapshot_type": context_data.get("snapshot_type", "incremental"),
                "timeframe": context_data.get("timeframe", "recent"),
                "source": "user_context",
                "tags": [],
                "confidence_score": 1.0,
                "doc_version": 1,
            },
        }

        # Use existing ingest_one function
        start_time = time.perf_counter()
        chunk_count = ingest_one(ingest_payload)
        processing_time_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Context vectorized and ingested: user_id={} chunks={} time={}ms",
            user_id,
            chunk_count,
            round(processing_time_ms, 2),
        )

        return {
            "status": "completed",
            "doc_id": ingest_payload["doc_id"],
            "chunk_count": chunk_count,
            "processing_time_ms": processing_time_ms,
            "collection": "user_context",
        }

    except Exception as e:
        logger.error("Failed to vectorize context: user_id={} error={}", user_id, e, exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "error_type": type(e).__name__,
        }


# ============================================================================
# EVENT HANDLERS
# ============================================================================

# Global publisher for emitting downstream events
publisher = EventPublisher()


def handle_mood_created(event: MoodCreatedEvent):
    """
    Handle user.mood.created event.

    Flow:
    1. Receive mood event
    2. Aggregate context
    3. Publish context.aggregated event
    """
    logger.info(
        "Processing mood event: user_id={} event_id={} trace_id={}",
        event.user_id,
        event.event_id,
        event.trace_id,
    )

    try:
        # Aggregate context
        context_data = aggregate_user_context(
            user_id=event.user_id,
            event_data=event.data,
            event_type=event.event_type,
        )

        # Publish context.aggregated event
        context_event = ContextAggregatedEvent(
            user_id=event.user_id,
            trace_id=event.trace_id,
            context_data=context_data,
        )

        publisher.publish(context_event)

        logger.info(
            "Context aggregated and published: user_id={} event_id={}",
            event.user_id,
            context_event.event_id,
        )

    except Exception as e:
        logger.error(
            "Failed to process mood event: user_id={} event_id={} error={}",
            event.user_id,
            event.event_id,
            e,
            exc_info=True,
        )
        # Don't re-raise - we want the consumer to continue processing


def handle_activity_created(event: ActivityCreatedEvent):
    """
    Handle user.activity.created event.

    Flow:
    1. Receive activity event
    2. Aggregate context
    3. Publish context.aggregated event
    """
    logger.info(
        "Processing activity event: user_id={} event_id={} trace_id={}",
        event.user_id,
        event.event_id,
        event.trace_id,
    )

    try:
        # Aggregate context
        context_data = aggregate_user_context(
            user_id=event.user_id,
            event_data=event.data,
            event_type=event.event_type,
        )

        # Publish context.aggregated event
        context_event = ContextAggregatedEvent(
            user_id=event.user_id,
            trace_id=event.trace_id,
            context_data=context_data,
        )

        publisher.publish(context_event)

        logger.info(
            "Context aggregated and published: user_id={} event_id={}",
            event.user_id,
            context_event.event_id,
        )

    except Exception as e:
        logger.error(
            "Failed to process activity event: user_id={} event_id={} error={}",
            event.user_id,
            event.event_id,
            e,
            exc_info=True,
        )
        # Don't re-raise - we want the consumer to continue processing


def handle_context_aggregated(event: ContextAggregatedEvent):
    """
    Handle context.aggregated event.

    Flow:
    1. Receive aggregated context
    2. Vectorize using existing embeddings
    3. Ingest into Qdrant using existing pipeline
    4. Publish context.vectorized event
    """
    logger.info(
        "Processing context aggregation: user_id={} event_id={} trace_id={}",
        event.user_id,
        event.event_id,
        event.trace_id,
    )

    try:
        # Vectorize and ingest
        result = vectorize_context(
            context_data=event.context_data,
            user_id=event.user_id,
            trace_id=event.trace_id,
        )

        if result["status"] == "completed":
            # Get the embeddings that were generated (for event payload)
            # Note: In production, you might want to return vectors from vectorize_context
            # For now, we'll just indicate success

            # Publish context.vectorized event
            vectorized_event = ContextVectorizedEvent(
                user_id=event.user_id,
                trace_id=event.trace_id,
                context_data=event.context_data,
                vectors=[],  # Could include actual vectors if needed downstream
                embedding_model=settings.embedding_model,
                embedding_version=service_settings.embedding_version,
            )

            publisher.publish(vectorized_event)

            logger.info(
                "Context vectorized and published: user_id={} doc_id={} chunks={}",
                event.user_id,
                result["doc_id"],
                result["chunk_count"],
            )
        else:
            logger.warning(
                "Context vectorization skipped or failed: user_id={} status={}",
                event.user_id,
                result["status"],
            )

    except Exception as e:
        logger.error(
            "Failed to vectorize context: user_id={} event_id={} error={}",
            event.user_id,
            event.event_id,
            e,
            exc_info=True,
        )
        # Don't re-raise - we want the consumer to continue processing


# ============================================================================
# MAIN CONSUMER
# ============================================================================

def main():
    """
    Main entry point for Kafka consumer.

    Subscribes to:
    - aura360.user.events (mood, activity)
    - aura360.context.aggregated (vectorization)

    Graceful shutdown on SIGTERM/SIGINT.
    """
    logger.info("🚀 Starting Vectordb Kafka Consumer")
    logger.info("   Embedding Model: {}", settings.embedding_model)
    logger.info("   Qdrant URL: {}", settings.qdrant_url)
    logger.info("   Collection: {}", settings.collection_name)

    # Create event handler with decorator-style registration
    handler = EventHandler(
        group_id="vectordb-context-processor",
        topics=["aura360.user.events", "aura360.context.aggregated"],
        auto_commit=True,
    )

    # Register handlers
    handler.consumer.register_handler("user.mood.created", handle_mood_created)
    handler.consumer.register_handler("user.activity.created", handle_activity_created)
    handler.consumer.register_handler("context.aggregated", handle_context_aggregated)

    logger.info("📥 Registered handlers:")
    logger.info("   - user.mood.created → aggregate context")
    logger.info("   - user.activity.created → aggregate context")
    logger.info("   - context.aggregated → vectorize and ingest")
    logger.info("")
    logger.info("🎧 Consumer ready, waiting for events...")
    logger.info("   Press Ctrl+C to stop")

    # Setup graceful shutdown
    def shutdown_handler(signum, frame):
        logger.info("Received shutdown signal, closing consumer...")
        handler.stop()
        publisher.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    try:
        # Start consuming (blocking)
        handler.start()
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error("Consumer crashed: {}", e, exc_info=True)
        sys.exit(1)
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
