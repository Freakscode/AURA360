"""
Messaging Backend Abstraction

Permite cambiar entre Kafka y Celery usando feature flags.
"""

import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Optional

from .events import BaseEvent


class MessagingBackend(str, Enum):
    """Available messaging backends"""
    KAFKA = "kafka"
    CELERY = "celery"
    DISABLED = "disabled"  # Para testing o fallback total


class MessageBroker(ABC):
    """Abstract interface para message broker"""

    @abstractmethod
    def publish(self, event: BaseEvent, topic: Optional[str] = None) -> None:
        """Publish an event"""
        pass

    @abstractmethod
    def register_handler(self, event_type: str, handler: Callable) -> None:
        """Register a handler for an event type"""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start consuming (blocking)"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close connections"""
        pass


class KafkaBackend(MessageBroker):
    """Kafka implementation"""

    def __init__(self, kafka_config=None):
        from .producer import EventPublisher
        from .consumer import EventConsumer

        self.publisher = EventPublisher(kafka_config=kafka_config)
        self.consumer = None  # Lazy init

    def publish(self, event: BaseEvent, topic: Optional[str] = None) -> None:
        self.publisher.publish(event, topic=topic)

    def register_handler(self, event_type: str, handler: Callable) -> None:
        if self.consumer is None:
            raise RuntimeError("Consumer not initialized. Call start() first.")
        self.consumer.register_handler(event_type, handler)

    def start(self) -> None:
        # Implemented by specific consumers
        raise NotImplementedError("Use EventConsumer directly for Kafka consumers")

    def close(self) -> None:
        self.publisher.close()
        if self.consumer:
            self.consumer.close()


class CeleryBackend(MessageBroker):
    """
    Celery implementation (fallback)

    Uses Celery tasks to simulate event publishing/consuming.
    """

    def __init__(self, celery_app=None):
        if celery_app is None:
            try:
                from config.celery import app as django_celery_app
                celery_app = django_celery_app
            except ModuleNotFoundError:
                from celery import current_app as celery_current_app

                celery_app = celery_current_app

        self.celery_app = celery_app
        self.handlers = {}

    def publish(self, event: BaseEvent, topic: Optional[str] = None) -> None:
        """
        Publish event via Celery task

        Maps event types to Celery tasks:
        - user.mood.created → tasks.process_mood_created.delay(event)
        - context.aggregated → tasks.process_context_aggregated.delay(event)
        """
        import logging
        logger = logging.getLogger(__name__)

        # Serialize event
        event_dict = event.dict()

        # Map event type to Celery task
        task_name = self._get_task_name(event.event_type)

        if self.celery_app and task_name:
            try:
                self.celery_app.send_task(task_name, args=[event_dict])
                logger.debug(f"Published event {event.event_type} via Celery task {task_name}")
            except Exception as e:
                logger.error(f"Failed to publish event via Celery: {e}", exc_info=True)
        else:
            logger.warning(f"No Celery task mapping for event type: {event.event_type}")

    def register_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register handler (stored but not actively used in Celery mode)

        In Celery mode, handlers are defined as @celery.task decorators,
        not registered dynamically.
        """
        self.handlers[event_type] = handler

    def start(self) -> None:
        """Not applicable for Celery (workers started separately)"""
        pass

    def close(self) -> None:
        """Not applicable for Celery"""
        pass

    def _get_task_name(self, event_type: str) -> Optional[str]:
        """
        Map event type to Celery task name

        Override this in subclass or configure via environment
        """
        # Default mapping
        task_map = {
            "user.mood.created": "vectosvc.worker.tasks.process_mood_created",
            "user.activity.created": "vectosvc.worker.tasks.process_activity_created",
            "context.aggregated": "vectosvc.worker.tasks.process_context_aggregated",
            "context.vectorized": "vectosvc.worker.tasks.ingest_vectors",
        }
        return task_map.get(event_type)


class DisabledBackend(MessageBroker):
    """
    Disabled backend (no-op)

    Useful for testing or when messaging is temporarily disabled.
    """

    def publish(self, event: BaseEvent, topic: Optional[str] = None) -> None:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Messaging disabled: Event {event.event_type} not published")

    def register_handler(self, event_type: str, handler: Callable) -> None:
        pass

    def start(self) -> None:
        pass

    def close(self) -> None:
        pass


# ============================================================================
# FACTORY
# ============================================================================


def get_messaging_backend() -> MessageBroker:
    """
    Factory function to get the appropriate messaging backend

    Determined by environment variable: MESSAGING_BACKEND

    Environment Variables:
        MESSAGING_BACKEND: "kafka" | "celery" | "disabled"
        Default: "kafka"
    """
    backend_type = os.getenv("MESSAGING_BACKEND", "kafka").lower()

    if backend_type == MessagingBackend.KAFKA:
        from .config import get_kafka_config
        return KafkaBackend(kafka_config=get_kafka_config())

    elif backend_type == MessagingBackend.CELERY:
        # Import Celery app from service
        try:
            from celery import current_app
            return CeleryBackend(celery_app=current_app)
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Celery not available, falling back to disabled backend")
            return DisabledBackend()

    elif backend_type == MessagingBackend.DISABLED:
        return DisabledBackend()

    else:
        raise ValueError(f"Unknown messaging backend: {backend_type}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_default_backend: Optional[MessageBroker] = None


def publish_event(event: BaseEvent, topic: Optional[str] = None) -> None:
    """
    Publish an event using the configured backend

    Automatically uses Kafka or Celery based on MESSAGING_BACKEND env var.
    """
    global _default_backend
    if _default_backend is None:
        _default_backend = get_messaging_backend()

    _default_backend.publish(event, topic=topic)


def get_backend() -> MessageBroker:
    """Get the default messaging backend (singleton)"""
    global _default_backend
    if _default_backend is None:
        _default_backend = get_messaging_backend()
    return _default_backend
