"""
Event Publisher for Kafka

Provides a high-level interface for publishing events to Kafka topics.
Handles serialization, delivery guarantees, and error handling.
"""

import json
import logging
from typing import Optional, Callable

from confluent_kafka import Producer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from .config import get_kafka_config
from .events import BaseEvent, EventType

logger = logging.getLogger(__name__)


class EventPublisher:
    """
    Publisher for sending events to Kafka topics.

    Features:
    - Automatic JSON serialization
    - Delivery guarantees (acks=all)
    - Idempotency (duplicate prevention)
    - Automatic topic creation
    - Error handling and retries
    """

    # Topic mapping based on event type
    TOPIC_MAP = {
        EventType.USER_MOOD_CREATED: "aura360.user.events",
        EventType.USER_ACTIVITY_CREATED: "aura360.user.events",
        EventType.USER_IKIGAI_UPDATED: "aura360.user.events",
        EventType.USER_PROFILE_UPDATED: "aura360.user.events",
        EventType.CONTEXT_AGGREGATED: "aura360.context.aggregated",
        EventType.CONTEXT_VECTORIZED: "aura360.context.vectorized",
        EventType.GUARDIAN_REQUEST: "aura360.guardian.requests",
        EventType.GUARDIAN_RESPONSE: "aura360.guardian.responses",
        EventType.GUARDIAN_RESPONSE_CHUNK: "aura360.guardian.responses",
        EventType.VECTORDB_INGEST_REQUESTED: "aura360.vectordb.ingest",
        EventType.VECTORDB_INGEST_COMPLETED: "aura360.vectordb.ingest",
        EventType.VECTORDB_INGEST_FAILED: "aura360.vectordb.ingest",
    }

    def __init__(
        self,
        kafka_config=None,
        delivery_callback: Optional[Callable] = None
    ):
        """
        Initialize the event publisher.

        Args:
            kafka_config: KafkaConfig instance (optional, will use default from env)
            delivery_callback: Optional callback for delivery reports
        """
        self.config = kafka_config or get_kafka_config()
        self.producer = Producer(self.config.to_producer_config())
        self.delivery_callback = delivery_callback or self._default_delivery_callback

        logger.info(
            f"EventPublisher initialized with brokers: {self.config.bootstrap_servers}"
        )

    def publish(
        self,
        event: BaseEvent,
        topic: Optional[str] = None,
        key: Optional[str] = None
    ) -> None:
        """
        Publish an event to Kafka.

        Args:
            event: Event instance to publish
            topic: Optional topic override (defaults to TOPIC_MAP based on event_type)
            key: Optional partition key (defaults to user_id if present)

        Raises:
            KafkaException: If publishing fails after retries
        """
        # Determine topic
        if topic is None:
            topic = self.TOPIC_MAP.get(event.event_type)
            if topic is None:
                raise ValueError(f"No topic mapping for event type: {event.event_type}")

        # Determine key (for partitioning)
        if key is None and event.user_id:
            key = event.user_id

        # Serialize event to JSON
        value = self._serialize_event(event)

        try:
            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=value,
                on_delivery=self.delivery_callback,
                headers={
                    'event_type': event.event_type.value,
                    'event_id': str(event.event_id),
                    'trace_id': event.trace_id or '',
                }
            )

            # Trigger delivery reports (non-blocking)
            self.producer.poll(0)

            logger.debug(
                f"Published event {event.event_type} to topic {topic}",
                extra={
                    'event_id': str(event.event_id),
                    'event_type': event.event_type,
                    'topic': topic,
                    'user_id': event.user_id,
                }
            )

        except BufferError:
            # Local queue is full, wait and retry
            logger.warning("Producer queue full, flushing...")
            self.producer.flush(timeout=10)
            self.produce(event, topic, key)  # Retry

        except KafkaException as e:
            logger.error(
                f"Failed to publish event {event.event_type}: {e}",
                exc_info=True,
                extra={
                    'event_id': str(event.event_id),
                    'event_type': event.event_type,
                    'topic': topic,
                }
            )
            raise

    def flush(self, timeout: float = 10.0) -> int:
        """
        Flush pending messages.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Number of messages still in queue
        """
        remaining = self.producer.flush(timeout=timeout)
        if remaining > 0:
            logger.warning(f"{remaining} messages still in queue after flush")
        return remaining

    def close(self):
        """Close the producer and flush all pending messages"""
        logger.info("Closing EventPublisher...")
        remaining = self.flush(timeout=30)
        if remaining > 0:
            logger.error(f"Failed to deliver {remaining} messages before closing")

    def _serialize_event(self, event: BaseEvent) -> bytes:
        """Serialize event to JSON bytes"""
        json_str = event.json()
        return json_str.encode('utf-8')

    def _default_delivery_callback(self, err, msg):
        """Default callback for delivery reports"""
        if err is not None:
            logger.error(
                f"Message delivery failed: {err}",
                extra={
                    'topic': msg.topic(),
                    'partition': msg.partition(),
                    'offset': msg.offset(),
                }
            )
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}"
            )

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_default_publisher: Optional[EventPublisher] = None


def get_publisher() -> EventPublisher:
    """Get or create the default event publisher (singleton)"""
    global _default_publisher
    if _default_publisher is None:
        _default_publisher = EventPublisher()
    return _default_publisher


def publish_event(event: BaseEvent, topic: Optional[str] = None) -> None:
    """
    Convenience function to publish an event using the default publisher.

    Args:
        event: Event instance to publish
        topic: Optional topic override
    """
    publisher = get_publisher()
    publisher.publish(event, topic=topic)
