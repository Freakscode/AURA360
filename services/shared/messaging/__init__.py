"""
AURA360 Shared Messaging Module

Provides abstractions for event-driven communication using Kafka.
Can be imported by any service (Django API, Vectordb, Agents).

Supports hybrid mode: Kafka (default) or Celery (fallback) via MESSAGING_BACKEND env var.
"""

from .producer import EventPublisher
from .consumer import EventConsumer, EventHandler
from .events import (
    UserEvent,
    ContextEvent,
    GuardianEvent,
    VectordbEvent,
    EventType,
)
from .config import KafkaConfig
from .backend import (
    MessagingBackend,
    MessageBroker,
    get_messaging_backend,
    publish_event,
    get_backend,
)

__all__ = [
    # Kafka-specific (direct usage)
    "EventPublisher",
    "EventConsumer",
    "EventHandler",
    "KafkaConfig",

    # Events
    "UserEvent",
    "ContextEvent",
    "GuardianEvent",
    "VectordbEvent",
    "EventType",

    # Hybrid backend (recommended)
    "MessagingBackend",
    "MessageBroker",
    "get_messaging_backend",
    "publish_event",
    "get_backend",
]

__version__ = "1.1.0"
