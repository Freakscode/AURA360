"""
Test script for Vectordb Kafka Consumer

Validates that the consumer correctly:
1. Receives user.mood.created events
2. Aggregates context
3. Publishes context.aggregated events
4. Vectorizes context
5. Stores in Qdrant

Usage:
    # Terminal 1: Start consumer
    uv run python -m vectosvc.kafka.consumer

    # Terminal 2: Run this test
    uv run python test_kafka_consumer.py
"""

from messaging import EventPublisher
from messaging.events import MoodCreatedEvent
import time


def main():
    print("=" * 60)
    print("Vectordb Kafka Consumer Test")
    print("=" * 60)
    print()
    print("This test will:")
    print("1. Publish a user.mood.created event")
    print("2. Wait for consumer to process it")
    print("3. Verify context.aggregated and context.vectorized events")
    print()
    print("Make sure the consumer is running in another terminal:")
    print("  cd services/vectordb")
    print("  uv run python -m vectosvc.kafka.consumer")
    print()
    input("Press Enter to continue...")
    print()

    # Create publisher
    publisher = EventPublisher()

    # Create test mood event
    event = MoodCreatedEvent.from_mood_entry(
        user_id="test-user-kafka-001",
        mood_data={
            "mood_score": 9,
            "tags": ["energetic", "focused", "grateful"],
            "notes": "Great day! Completed all my tasks and had a productive workout.",
            "created_at": "2025-01-07T14:30:00Z",
        },
        trace_id="test-trace-vectordb-001",
    )

    print(f"Publishing event: {event.event_type}")
    print(f"  Event ID: {event.event_id}")
    print(f"  User ID: {event.user_id}")
    print(f"  Trace ID: {event.trace_id}")
    print(f"  Mood Score: {event.data['mood_score']}")
    print(f"  Tags: {event.data['tags']}")
    print()

    # Publish
    publisher.publish(event)

    print("Event published successfully!")
    print()
    print("Check the consumer logs for:")
    print("  1. 'Processing mood event' message")
    print("  2. 'Context aggregated and published' message")
    print("  3. 'Context vectorized and published' message")
    print()
    print("You can also verify in Kafka UI:")
    print("  http://localhost:8090")
    print("  - Topic: aura360.user.events (should have 1 new message)")
    print("  - Topic: aura360.context.aggregated (should have 1 new message)")
    print("  - Topic: aura360.context.vectorized (should have 1 new message)")
    print()
    print("And in Qdrant:")
    print("  http://localhost:6333/dashboard")
    print("  - Collection: user_context (should have new vectors)")

    publisher.close()


if __name__ == "__main__":
    main()
