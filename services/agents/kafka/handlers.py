"""
Guardian Request Handlers for Kafka

Handles incoming GuardianRequestEvent and executes Guardian logic using
existing HolisticAdviceService, then publishes GuardianResponseEvent.
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.holistic import AdviceRequest, HolisticAdviceService
from services.exceptions import ServiceError

logger = logging.getLogger(__name__)


class GuardianRequestHandler:
    """
    Handles GuardianRequestEvent from Kafka.

    Executes Guardian advice generation using existing HolisticAdviceService
    and publishes GuardianResponseEvent with correlation ID.
    """

    def __init__(self, service: Optional[HolisticAdviceService] = None):
        """
        Initialize handler with HolisticAdviceService.

        Args:
            service: Optional pre-configured HolisticAdviceService
        """
        self.service = service or HolisticAdviceService()
        logger.info("GuardianRequestHandler initialized")

    def handle(self, event: dict[str, Any], publisher: Any) -> None:
        """
        Handle GuardianRequestEvent and publish response.

        Args:
            event: Deserialized GuardianRequestEvent as dictionary
            publisher: EventPublisher instance for publishing response
        """
        start_time = time.time()
        request_id = event.get("request_id")
        trace_id = event.get("trace_id", str(request_id))
        user_id = event.get("user_id")
        guardian_type = event.get("guardian_type", "holistic")
        query = event.get("query", "")
        context = event.get("context", {})

        logger.info(
            f"Processing GuardianRequestEvent",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "user_id": user_id,
                "guardian_type": guardian_type,
            },
        )

        try:
            # Map guardian_type to category for HolisticAdviceService
            category_mapping = {
                "mental": "mind",
                "physical": "body",
                "spiritual": "soul",
                "holistic": "holistic",
            }
            category = category_mapping.get(guardian_type, "holistic")

            # Extract user_profile from context
            user_profile = context.get("user_profile", {})
            if not user_profile.get("id"):
                user_profile["id"] = user_id

            # Build AdviceRequest
            advice_request = AdviceRequest(
                trace_id=trace_id,
                category=category,
                user_profile=user_profile,
                preferences=context.get("preferences"),
                context=query,
            )

            # Execute Guardian logic using existing service
            response_data = self.service.generate_advice(advice_request)

            # Extract relevant data for response
            if response_data.get("status") == "success":
                data = response_data.get("data", {})
                summary = data.get("summary", "")
                recommendations = data.get("recommendations", [])
                agent_runs = data.get("agent_runs", [])

                # Calculate confidence score (average from recommendations)
                confidence_scores = [
                    rec.get("confidence", 0.0)
                    for rec in recommendations
                    if rec.get("confidence") is not None
                ]
                avg_confidence = (
                    sum(confidence_scores) / len(confidence_scores)
                    if confidence_scores
                    else 0.8
                )

                # Extract retrieval context from agent_runs
                retrieval_context = []
                for run in agent_runs:
                    vector_queries = run.get("vector_queries", [])
                    for vq in vector_queries:
                        response_payload = vq.get("response_payload", {})
                        hits = response_payload.get("hits", [])
                        retrieval_context.extend(
                            {
                                "text": hit.get("payload", {}).get("text", ""),
                                "score": hit.get("score", 0.0),
                                "metadata": hit.get("payload", {}),
                            }
                            for hit in hits
                        )

                processing_time_ms = (time.time() - start_time) * 1000

                # Build GuardianResponseEvent
                response_event = {
                    "event_type": "guardian.response",
                    "event_id": None,  # Will be auto-generated
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "trace_id": trace_id,
                    "user_id": user_id,
                    "guardian_type": guardian_type,
                    "request_id": request_id,
                    "response": summary,
                    "recommendations": recommendations,
                    "confidence_score": avg_confidence,
                    "retrieval_context": retrieval_context[:5],  # Top 5 contexts
                    "processing_time_ms": processing_time_ms,
                    "metadata": {
                        "category": category,
                        "agent_runs": len(agent_runs),
                    },
                }

                # Publish response event
                self._publish_response(publisher, response_event)

                logger.info(
                    f"Successfully processed GuardianRequestEvent",
                    extra={
                        "request_id": request_id,
                        "trace_id": trace_id,
                        "processing_time_ms": processing_time_ms,
                        "confidence_score": avg_confidence,
                    },
                )

            else:
                # Handle error response from service
                error_data = response_data.get("error", {})
                self._publish_error_response(
                    publisher=publisher,
                    request_id=request_id,
                    trace_id=trace_id,
                    user_id=user_id,
                    guardian_type=guardian_type,
                    error_message=error_data.get("message", "Unknown error"),
                    error_type=error_data.get("type", "service_error"),
                    processing_time_ms=(time.time() - start_time) * 1000,
                )

        except ServiceError as exc:
            logger.warning(
                f"ServiceError processing GuardianRequestEvent",
                extra={
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "error_type": exc.error.type,
                },
            )
            self._publish_error_response(
                publisher=publisher,
                request_id=request_id,
                trace_id=trace_id,
                user_id=user_id,
                guardian_type=guardian_type,
                error_message=exc.error.message,
                error_type=exc.error.type,
                processing_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as exc:
            logger.exception(
                f"Unexpected error processing GuardianRequestEvent",
                extra={
                    "request_id": request_id,
                    "trace_id": trace_id,
                },
            )
            self._publish_error_response(
                publisher=publisher,
                request_id=request_id,
                trace_id=trace_id,
                user_id=user_id,
                guardian_type=guardian_type,
                error_message="Internal processing error",
                error_type="unhandled_error",
                processing_time_ms=(time.time() - start_time) * 1000,
            )

    def _publish_response(self, publisher: Any, response_event: dict[str, Any]) -> None:
        """
        Publish GuardianResponseEvent to Kafka.

        Args:
            publisher: EventPublisher instance
            response_event: Response event data
        """
        try:
            # Import here to avoid circular imports
            from uuid import uuid4

            # Generate event_id if not present
            if response_event.get("event_id") is None:
                response_event["event_id"] = str(uuid4())

            # Publish to aura360.guardian.responses topic
            publisher.produce(
                topic="aura360.guardian.responses",
                key=str(response_event.get("request_id")),
                value=response_event,
                headers={
                    "event_type": "guardian.response",
                    "request_id": str(response_event.get("request_id")),
                    "trace_id": response_event.get("trace_id", ""),
                },
            )

            logger.debug(
                f"Published GuardianResponseEvent",
                extra={
                    "request_id": response_event.get("request_id"),
                    "trace_id": response_event.get("trace_id"),
                },
            )

        except Exception as exc:
            logger.error(
                f"Failed to publish GuardianResponseEvent: {exc}",
                exc_info=True,
                extra={
                    "request_id": response_event.get("request_id"),
                    "trace_id": response_event.get("trace_id"),
                },
            )

    def _publish_error_response(
        self,
        publisher: Any,
        request_id: str,
        trace_id: str,
        user_id: str,
        guardian_type: str,
        error_message: str,
        error_type: str,
        processing_time_ms: float,
    ) -> None:
        """
        Publish error response event.

        Args:
            publisher: EventPublisher instance
            request_id: Correlation ID from request
            trace_id: Trace ID for distributed tracing
            user_id: User ID
            guardian_type: Type of guardian
            error_message: Error message
            error_type: Error type
            processing_time_ms: Processing time in milliseconds
        """
        from uuid import uuid4

        error_event = {
            "event_type": "guardian.response",
            "event_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "user_id": user_id,
            "guardian_type": guardian_type,
            "request_id": request_id,
            "response": error_message,
            "recommendations": [],
            "confidence_score": 0.0,
            "retrieval_context": [],
            "processing_time_ms": processing_time_ms,
            "metadata": {
                "error": True,
                "error_type": error_type,
                "error_message": error_message,
            },
        }

        self._publish_response(publisher, error_event)
