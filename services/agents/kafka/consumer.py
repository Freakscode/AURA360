"""
Guardian Kafka Consumer

Standalone consumer service that listens to aura360.guardian.requests topic,
processes Guardian requests using HolisticAdviceService, and publishes responses
to aura360.guardian.responses topic.

Usage:
    python -m kafka.consumer
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from confluent_kafka import Consumer, Producer, KafkaError
from infra.env import load_environment
from services.holistic import HolisticAdviceService

from .handlers import GuardianRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GuardianConsumerService:
    """
    Kafka consumer service for Guardian requests.

    Subscribes to aura360.guardian.requests topic and processes incoming
    GuardianRequestEvent using GuardianRequestHandler.
    """

    def __init__(self):
        """Initialize consumer service with Kafka configuration."""
        load_environment(override=False)

        # Kafka configuration
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.group_id = "aura360-guardian-consumer"
        self.topics = ["aura360.guardian.requests"]

        # Consumer configuration
        consumer_config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "client.id": f"guardian-consumer-{os.getpid()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
            "auto.commit.interval.ms": 5000,
            "max.poll.interval.ms": 300000,  # 5 minutes
            "session.timeout.ms": 45000,  # 45 seconds
        }

        # Producer configuration for publishing responses
        producer_config = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": f"guardian-producer-{os.getpid()}",
            "acks": "all",
            "retries": 3,
            "enable.idempotence": True,
        }

        self.consumer = Consumer(consumer_config)
        self.producer = Producer(producer_config)
        self.running = False

        # Initialize handler
        self.handler = GuardianRequestHandler()

        logger.info(
            f"GuardianConsumerService initialized",
            extra={
                "group_id": self.group_id,
                "topics": self.topics,
                "bootstrap_servers": self.bootstrap_servers,
            },
        )

    def start(self) -> None:
        """Start consuming events from Kafka."""
        self.consumer.subscribe(self.topics)
        self.running = True

        logger.info(
            f"GuardianConsumerService started, listening to topics: {self.topics}"
        )

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

        except Exception as exc:
            logger.error(f"Consumer error: {exc}", exc_info=True)
            raise

        finally:
            self.close()

    def stop(self) -> None:
        """Stop the consumer loop gracefully."""
        logger.info("Stopping GuardianConsumerService...")
        self.running = False

    def close(self) -> None:
        """Close consumer and producer connections."""
        logger.info("Closing GuardianConsumerService...")
        try:
            # Flush producer
            remaining = self.producer.flush(timeout=10)
            if remaining > 0:
                logger.warning(f"{remaining} messages still in queue after flush")

            # Close consumer
            self.consumer.close()

            logger.info("GuardianConsumerService closed successfully")

        except Exception as exc:
            logger.error(f"Error closing consumer: {exc}", exc_info=True)

    def _process_message(self, msg) -> None:
        """
        Process a single Kafka message.

        Args:
            msg: Kafka message containing GuardianRequestEvent
        """
        try:
            # Extract headers
            headers = {k: v.decode("utf-8") for k, v in (msg.headers() or [])}
            event_type = headers.get("event_type")

            # Deserialize message
            value = msg.value().decode("utf-8")
            event_data = json.loads(value)

            logger.info(
                f"Received event {event_type}",
                extra={
                    "event_type": event_type,
                    "request_id": event_data.get("request_id"),
                    "trace_id": event_data.get("trace_id"),
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                },
            )

            # Process Guardian request
            if event_type == "guardian.request":
                self.handler.handle(event_data, self.producer)
            else:
                logger.warning(
                    f"Unknown event type: {event_type}",
                    extra={"event_type": event_type},
                )

        except json.JSONDecodeError as exc:
            logger.error(
                f"Failed to decode JSON message: {exc}",
                exc_info=True,
                extra={
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                },
            )

        except Exception as exc:
            logger.error(
                f"Error processing message: {exc}",
                exc_info=True,
                extra={
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                },
            )

    def _handle_error(self, msg) -> None:
        """Handle Kafka errors."""
        error = msg.error()

        if error.code() == KafkaError._PARTITION_EOF:
            logger.debug(f"Reached end of partition: {msg.topic()} [{msg.partition()}]")

        elif error.code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
            logger.error(f"Unknown topic or partition: {error}")
            self.stop()

        else:
            logger.error(f"Kafka error: {error}")


def main():
    """Main entry point for Guardian consumer service."""
    logger.info("Starting AURA360 Guardian Consumer Service...")

    consumer_service = GuardianConsumerService()

    try:
        consumer_service.start()
    except Exception as exc:
        logger.error(f"Fatal error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
