"""
Guardian Response Consumer

Listens to aura360.guardian.responses topic and stores responses in Redis
for API polling.

Usage:
    python -m kafka.response_consumer
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import redis
from confluent_kafka import Consumer, KafkaError

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.env import load_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GuardianResponseConsumer:
    """
    Consumer that listens to Guardian responses and stores them in Redis.

    This allows the API to poll for responses using request_id.
    """

    def __init__(self):
        """Initialize response consumer."""
        load_environment(override=False)

        # Kafka configuration
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.group_id = "aura360-guardian-response-consumer"
        self.topics = ["aura360.guardian.responses"]

        # Consumer configuration
        consumer_config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "client.id": f"guardian-response-consumer-{os.getpid()}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
            "auto.commit.interval.ms": 5000,
        }

        self.consumer = Consumer(consumer_config)
        self.running = False

        # Redis client
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

        # TTL for responses in Redis (30 minutes)
        self.response_ttl = int(os.getenv("GUARDIAN_RESPONSE_TTL", "1800"))

        logger.info(
            f"GuardianResponseConsumer initialized",
            extra={
                "group_id": self.group_id,
                "topics": self.topics,
                "bootstrap_servers": self.bootstrap_servers,
                "redis_url": redis_url,
                "response_ttl": self.response_ttl,
            },
        )

    def start(self) -> None:
        """Start consuming Guardian responses."""
        self.consumer.subscribe(self.topics)
        self.running = True

        logger.info(
            f"GuardianResponseConsumer started, listening to topics: {self.topics}"
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
        logger.info("Stopping GuardianResponseConsumer...")
        self.running = False

    def close(self) -> None:
        """Close consumer connection."""
        logger.info("Closing GuardianResponseConsumer...")
        try:
            self.consumer.close()
            logger.info("GuardianResponseConsumer closed successfully")

        except Exception as exc:
            logger.error(f"Error closing consumer: {exc}", exc_info=True)

    def _process_message(self, msg) -> None:
        """
        Process Guardian response message and store in Redis.

        Args:
            msg: Kafka message containing GuardianResponseEvent
        """
        try:
            # Extract headers
            headers = {k: v.decode("utf-8") for k, v in (msg.headers() or [])}
            event_type = headers.get("event_type")
            request_id = headers.get("request_id")

            # Deserialize message
            value = msg.value().decode("utf-8")
            response_data = json.loads(value)

            logger.info(
                f"Received Guardian response",
                extra={
                    "event_type": event_type,
                    "request_id": request_id,
                    "trace_id": response_data.get("trace_id"),
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                },
            )

            # Store in Redis with TTL
            if request_id:
                redis_key = f"guardian:response:{request_id}"
                self.redis_client.setex(
                    redis_key,
                    self.response_ttl,
                    json.dumps(response_data),
                )

                logger.info(
                    f"Stored Guardian response in Redis",
                    extra={
                        "request_id": request_id,
                        "redis_key": redis_key,
                        "ttl": self.response_ttl,
                    },
                )
            else:
                logger.warning(
                    f"Guardian response missing request_id",
                    extra={"response_data": response_data},
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
    """Main entry point for Guardian response consumer."""
    logger.info("Starting AURA360 Guardian Response Consumer...")

    consumer = GuardianResponseConsumer()

    try:
        consumer.start()
    except Exception as exc:
        logger.error(f"Fatal error: {exc}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
