"""
Test Guardian Request-Reply Flow via Kafka

This script demonstrates the complete request-reply pattern:
1. Publish GuardianRequestEvent to aura360.guardian.requests
2. Consumer processes request and publishes GuardianResponseEvent
3. Response consumer stores response in Redis
4. API polls Redis for response

Usage:
    # Start consumers first (in separate terminals):
    python -m kafka.consumer
    python -m kafka.response_consumer

    # Then run this test:
    python scripts/test_guardian_kafka_flow.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import redis
from confluent_kafka import Producer, Consumer, KafkaError

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infra.env import load_environment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GuardianKafkaFlowTester:
    """
    Test harness for Guardian request-reply pattern via Kafka.
    """

    def __init__(self):
        """Initialize tester with Kafka and Redis clients."""
        load_environment(override=False)

        # Kafka configuration
        bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

        # Producer configuration
        producer_config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": f"test-guardian-producer-{os.getpid()}",
            "acks": "all",
            "retries": 3,
            "enable.idempotence": True,
        }

        # Consumer configuration for responses
        consumer_config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": f"test-guardian-consumer-{uuid4()}",
            "client.id": f"test-guardian-consumer-{os.getpid()}",
            "auto.offset.reset": "latest",
            "enable.auto.commit": False,
        }

        self.producer = Producer(producer_config)
        self.consumer = Consumer(consumer_config)
        self.consumer.subscribe(["aura360.guardian.responses"])

        # Redis client
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

        logger.info(
            "GuardianKafkaFlowTester initialized",
            extra={
                "bootstrap_servers": bootstrap_servers,
                "redis_url": redis_url,
            },
        )

    def test_request_reply_flow(
        self,
        guardian_type: str = "mental",
        query: str = "¿Cómo puedo manejar el estrés laboral?",
        timeout: int = 60,
    ) -> dict:
        """
        Test complete request-reply flow.

        Args:
            guardian_type: Type of guardian (mental, physical, spiritual, holistic)
            query: User query
            timeout: Maximum wait time in seconds

        Returns:
            Dictionary with test results
        """
        request_id = str(uuid4())
        trace_id = f"test-{request_id[:8]}"
        user_id = "test-user-123"

        logger.info(
            f"Starting request-reply flow test",
            extra={
                "request_id": request_id,
                "trace_id": trace_id,
                "guardian_type": guardian_type,
            },
        )

        # Step 1: Publish GuardianRequestEvent
        start_time = time.time()
        event = self._build_request_event(
            request_id=request_id,
            trace_id=trace_id,
            user_id=user_id,
            guardian_type=guardian_type,
            query=query,
        )

        logger.info("Step 1: Publishing GuardianRequestEvent...")
        self._publish_request(event, request_id)
        publish_time = time.time() - start_time

        # Step 2: Poll for response via Kafka consumer
        logger.info("Step 2: Polling for GuardianResponseEvent from Kafka...")
        kafka_response = self._poll_kafka_response(request_id, timeout=timeout)
        kafka_poll_time = time.time() - start_time - publish_time

        # Step 3: Check Redis for stored response
        logger.info("Step 3: Checking Redis for stored response...")
        redis_response = self._check_redis_response(request_id)
        redis_check_time = time.time() - start_time - publish_time - kafka_poll_time

        total_time = time.time() - start_time

        # Build test results
        results = {
            "test_metadata": {
                "request_id": request_id,
                "trace_id": trace_id,
                "guardian_type": guardian_type,
                "query": query,
            },
            "timing": {
                "publish_time_ms": round(publish_time * 1000, 2),
                "kafka_poll_time_ms": round(kafka_poll_time * 1000, 2),
                "redis_check_time_ms": round(redis_check_time * 1000, 2),
                "total_time_ms": round(total_time * 1000, 2),
            },
            "kafka_response": kafka_response,
            "redis_response": redis_response,
            "correlation_verified": (
                kafka_response is not None
                and kafka_response.get("request_id") == request_id
            ),
            "success": (
                kafka_response is not None
                and redis_response is not None
                and kafka_response.get("request_id") == request_id
            ),
        }

        # Log results
        if results["success"]:
            logger.info(
                f"✓ Request-reply flow test PASSED",
                extra={
                    "request_id": request_id,
                    "total_time_ms": results["timing"]["total_time_ms"],
                    "correlation_verified": results["correlation_verified"],
                },
            )
        else:
            logger.error(
                f"✗ Request-reply flow test FAILED",
                extra={
                    "request_id": request_id,
                    "kafka_response_found": kafka_response is not None,
                    "redis_response_found": redis_response is not None,
                    "correlation_verified": results["correlation_verified"],
                },
            )

        return results

    def _build_request_event(
        self,
        request_id: str,
        trace_id: str,
        user_id: str,
        guardian_type: str,
        query: str,
    ) -> dict:
        """Build GuardianRequestEvent."""
        return {
            "event_type": "guardian.request",
            "event_id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "user_id": user_id,
            "guardian_type": guardian_type,
            "request_id": request_id,
            "query": query,
            "context": {
                "user_profile": {
                    "id": user_id,
                    "name": "Test User",
                    "age": 30,
                    "locale": "es",
                },
                "preferences": {
                    "focus": ["mindfulness", "stress management"],
                },
            },
        }

    def _publish_request(self, event: dict, request_id: str) -> None:
        """Publish GuardianRequestEvent to Kafka."""
        try:
            self.producer.produce(
                topic="aura360.guardian.requests",
                key=request_id.encode("utf-8"),
                value=json.dumps(event).encode("utf-8"),
                headers={
                    "event_type": "guardian.request",
                    "request_id": request_id,
                    "trace_id": event["trace_id"],
                },
            )
            self.producer.flush(timeout=5)

            logger.info(
                f"Published GuardianRequestEvent",
                extra={
                    "request_id": request_id,
                    "topic": "aura360.guardian.requests",
                },
            )

        except Exception as exc:
            logger.error(f"Failed to publish event: {exc}", exc_info=True)
            raise

    def _poll_kafka_response(
        self, request_id: str, timeout: int = 60
    ) -> dict | None:
        """
        Poll Kafka for GuardianResponseEvent.

        Args:
            request_id: Correlation ID to match
            timeout: Maximum wait time in seconds

        Returns:
            Response event dictionary or None
        """
        start_time = time.time()

        try:
            while (time.time() - start_time) < timeout:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    logger.error(f"Kafka error: {msg.error()}")
                    continue

                # Deserialize message
                headers = {k: v.decode("utf-8") for k, v in (msg.headers() or [])}
                response_request_id = headers.get("request_id")

                if response_request_id == request_id:
                    value = msg.value().decode("utf-8")
                    response_data = json.loads(value)

                    logger.info(
                        f"Received matching GuardianResponseEvent",
                        extra={
                            "request_id": request_id,
                            "elapsed_ms": round((time.time() - start_time) * 1000, 2),
                        },
                    )

                    return response_data

            logger.warning(
                f"Timeout waiting for GuardianResponseEvent",
                extra={"request_id": request_id, "timeout": timeout},
            )
            return None

        except Exception as exc:
            logger.error(f"Error polling Kafka: {exc}", exc_info=True)
            return None

    def _check_redis_response(self, request_id: str) -> dict | None:
        """
        Check Redis for stored response.

        Args:
            request_id: Correlation ID

        Returns:
            Response dictionary or None
        """
        try:
            redis_key = f"guardian:response:{request_id}"
            response_data = self.redis_client.get(redis_key)

            if response_data:
                response = json.loads(response_data)
                logger.info(
                    f"Found response in Redis",
                    extra={"request_id": request_id, "redis_key": redis_key},
                )
                return response

            logger.warning(
                f"Response not found in Redis",
                extra={"request_id": request_id, "redis_key": redis_key},
            )
            return None

        except Exception as exc:
            logger.error(f"Error checking Redis: {exc}", exc_info=True)
            return None

    def close(self):
        """Close connections."""
        logger.info("Closing GuardianKafkaFlowTester...")
        self.producer.flush(timeout=5)
        self.consumer.close()


def main():
    """Run Guardian request-reply flow tests."""
    print("\n" + "=" * 80)
    print("AURA360 Guardian Kafka Request-Reply Flow Test")
    print("=" * 80 + "\n")

    print("Prerequisites:")
    print("  1. Kafka running at localhost:9092")
    print("  2. Redis running at localhost:6379")
    print("  3. Guardian consumer running: python -m kafka.consumer")
    print("  4. Response consumer running: python -m kafka.response_consumer")
    print("\nStarting test in 3 seconds...\n")
    time.sleep(3)

    tester = GuardianKafkaFlowTester()

    try:
        # Test 1: Mental Guardian
        print("\n--- Test 1: Mental Guardian ---")
        results1 = tester.test_request_reply_flow(
            guardian_type="mental",
            query="¿Cómo puedo manejar el estrés laboral?",
            timeout=60,
        )
        print(f"\nResults:")
        print(f"  Success: {results1['success']}")
        print(f"  Correlation Verified: {results1['correlation_verified']}")
        print(f"  Total Time: {results1['timing']['total_time_ms']}ms")
        if results1["kafka_response"]:
            print(
                f"  Response Summary: {results1['kafka_response'].get('response', '')[:100]}..."
            )

        time.sleep(2)

        # Test 2: Physical Guardian
        print("\n--- Test 2: Physical Guardian ---")
        results2 = tester.test_request_reply_flow(
            guardian_type="physical",
            query="¿Qué ejercicios me recomiendas para mejorar mi postura?",
            timeout=60,
        )
        print(f"\nResults:")
        print(f"  Success: {results2['success']}")
        print(f"  Correlation Verified: {results2['correlation_verified']}")
        print(f"  Total Time: {results2['timing']['total_time_ms']}ms")

        # Summary
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        print(f"  Test 1 (Mental): {'✓ PASSED' if results1['success'] else '✗ FAILED'}")
        print(f"  Test 2 (Physical): {'✓ PASSED' if results2['success'] else '✗ FAILED'}")
        print(
            f"\n  Overall: {'✓ ALL TESTS PASSED' if results1['success'] and results2['success'] else '✗ SOME TESTS FAILED'}"
        )
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")

    except Exception as exc:
        logger.error(f"Test failed: {exc}", exc_info=True)
        sys.exit(1)

    finally:
        tester.close()


if __name__ == "__main__":
    main()
