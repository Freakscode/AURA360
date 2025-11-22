"""
Event Consumer for Kafka

Provides a high-level interface for consuming events from Kafka topics.
Handles deserialization, error recovery, and graceful shutdown.
"""

import json
import logging
import signal
import sys
from typing import Callable, List, Optional, Dict, Any

from confluent_kafka import Consumer, KafkaError, KafkaException, Message

from .config import get_kafka_config
from .events import BaseEvent, deserialize_event

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Consumer for receiving events from Kafka topics.

    Features:
    - Automatic JSON deserialization
    - Type-safe event handling
    - Graceful shutdown (SIGTERM/SIGINT)
    - Automatic error recovery
    - Commit strategies (auto/manual)
    """

    def __init__(
        self,
        group_id: str,
        topics: List[str],
        kafka_config=None,
        auto_commit: bool = True,
        **consumer_kwargs
    ):
        """
        Initialize the event consumer.

        Args:
            group_id: Consumer group ID
            topics: List of topics to subscribe to
            kafka_config: KafkaConfig instance (optional)
            auto_commit: Whether to auto-commit offsets
            **consumer_kwargs: Additional consumer configuration
        """
        self.group_id = group_id
        self.topics = topics
        self.config = kafka_config or get_kafka_config()
        self.running = False
        self.handlers: Dict[str, Callable[[BaseEvent], None]] = {}

        # Create consumer
        consumer_config = self.config.to_consumer_config(
            group_id=group_id,
            enable_auto_commit=auto_commit,
            **consumer_kwargs
        )
        self.consumer = Consumer(consumer_config)

        # Subscribe to topics
        self.consumer.subscribe(topics)

        logger.info(
            f"EventConsumer initialized: group={group_id}, topics={topics}",
            extra={'group_id': group_id, 'topics': topics}
        )

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[BaseEvent], None]
    ) -> None:
        """
        Register a handler function for a specific event type.

        Args:
            event_type: Event type string (e.g., "user.mood.created")
            handler: Callable that takes a BaseEvent and returns None
        """
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for event type: {event_type}")

    def start(self) -> None:
        """
        Start consuming events (blocking).

        This method will run indefinitely until stopped via signal or error.
        """
        self.running = True
        logger.info(f"Starting consumer loop for group: {self.group_id}")

        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    self._handle_error(msg)
                    continue

                self._process_message(msg)

        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")

        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
            raise

        finally:
            self.close()

    def stop(self) -> None:
        """Stop the consumer loop gracefully"""
        logger.info("Stopping consumer...")
        self.running = False

    def close(self) -> None:
        """Close the consumer and commit final offsets"""
        logger.info("Closing consumer...")
        try:
            self.consumer.close()
        except Exception as e:
            logger.error(f"Error closing consumer: {e}", exc_info=True)

    def _process_message(self, msg: Message) -> None:
        """
        Process a single message.

        Args:
            msg: Kafka message
        """
        try:
            # Extract headers
            headers = {k: v.decode('utf-8') for k, v in (msg.headers() or [])}
            event_type = headers.get('event_type')

            # Deserialize message
            value = msg.value().decode('utf-8')
            data = json.loads(value)

            # Deserialize into appropriate event class
            event = deserialize_event(event_type, data)

            logger.debug(
                f"Received event {event_type}",
                extra={
                    'event_type': event_type,
                    'event_id': str(event.event_id),
                    'topic': msg.topic(),
                    'partition': msg.partition(),
                    'offset': msg.offset(),
                }
            )

            # Call registered handler
            handler = self.handlers.get(event_type)
            if handler:
                handler(event)
            else:
                logger.warning(
                    f"No handler registered for event type: {event_type}",
                    extra={'event_type': event_type}
                )

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode JSON message: {e}",
                exc_info=True,
                extra={
                    'topic': msg.topic(),
                    'partition': msg.partition(),
                    'offset': msg.offset(),
                }
            )

        except Exception as e:
            logger.error(
                f"Error processing message: {e}",
                exc_info=True,
                extra={
                    'topic': msg.topic(),
                    'partition': msg.partition(),
                    'offset': msg.offset(),
                }
            )
            # Don't re-raise to avoid crashing the consumer
            # Message will be committed and we'll move on

    def _handle_error(self, msg: Message) -> None:
        """Handle Kafka errors"""
        error = msg.error()

        if error.code() == KafkaError._PARTITION_EOF:
            # End of partition, not an error
            logger.debug(
                f"Reached end of partition: {msg.topic()} [{msg.partition()}]"
            )

        elif error.code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
            logger.error(f"Unknown topic or partition: {error}")
            self.stop()

        else:
            logger.error(f"Kafka error: {error}")
            # For most errors, continue processing

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()


# ============================================================================
# DECORATOR-BASED CONSUMER
# ============================================================================


class EventHandler:
    """
    Decorator-based event handler for cleaner syntax.

    Usage:
        handler = EventHandler(group_id="my-service", topics=["aura360.user.events"])

        @handler.on("user.mood.created")
        def handle_mood_created(event: MoodCreatedEvent):
            print(f"Mood created: {event.data}")

        handler.start()
    """

    def __init__(self, group_id: str, topics: List[str], **kwargs):
        self.consumer = EventConsumer(group_id=group_id, topics=topics, **kwargs)

    def on(self, event_type: str):
        """
        Decorator to register a handler for an event type.

        Args:
            event_type: Event type string

        Returns:
            Decorator function
        """
        def decorator(func: Callable[[BaseEvent], None]):
            self.consumer.register_handler(event_type, func)
            return func
        return decorator

    def start(self):
        """Start the consumer loop"""
        self.consumer.start()

    def stop(self):
        """Stop the consumer"""
        self.consumer.stop()
