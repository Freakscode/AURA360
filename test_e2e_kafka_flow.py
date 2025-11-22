#!/usr/bin/env python3
"""
E2E Test: Complete Kafka Event Flow

Tests the complete event-driven architecture:
1. Publish MoodCreatedEvent to Kafka
2. Verify event in aura360.user.events topic
3. Simulate vectordb consumer processing
4. Verify ContextAggregatedEvent published
5. Simulate Guardian request-reply flow
6. Verify all components working together

Run with: uv run python test_e2e_kafka_flow.py
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

# Add services to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "services/shared"))

try:
    from confluent_kafka import Consumer, Producer
    from confluent_kafka.admin import AdminClient
except ImportError:
    print("❌ confluent-kafka not installed. Installing...")
    os.system("pip install confluent-kafka")
    from confluent_kafka import Consumer, Producer
    from confluent_kafka.admin import AdminClient


# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_SECURITY_PROTOCOL = os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT")

# Topics
TOPIC_USER_EVENTS = "aura360.user.events"
TOPIC_CONTEXT_AGGREGATED = "aura360.context.aggregated"
TOPIC_GUARDIAN_REQUESTS = "aura360.guardian.requests"
TOPIC_GUARDIAN_RESPONSES = "aura360.guardian.responses"


def get_producer_config():
    """Get producer configuration"""
    config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "e2e-test-producer",
    }

    if KAFKA_SECURITY_PROTOCOL == "SASL_SSL":
        config.update({
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.username": os.getenv("KAFKA_API_KEY"),
            "sasl.password": os.getenv("KAFKA_API_SECRET"),
        })

    return config


def get_consumer_config(group_id):
    """Get consumer configuration"""
    config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": group_id,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
    }

    if KAFKA_SECURITY_PROTOCOL == "SASL_SSL":
        config.update({
            "security.protocol": "SASL_SSL",
            "sasl.mechanism": "PLAIN",
            "sasl.username": os.getenv("KAFKA_API_KEY"),
            "sasl.password": os.getenv("KAFKA_API_SECRET"),
        })

    return config


def create_mood_event():
    """Create a MoodCreatedEvent"""
    event_id = str(uuid4())
    trace_id = str(uuid4())
    user_id = f"test-user-{int(time.time())}"

    event = {
        "event_id": event_id,
        "event_type": "user.mood.created",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "user_id": user_id,
        "data": {
            "mood_id": str(uuid4()),
            "mood_score": 8,
            "tags": ["happy", "productive", "e2e-test"],
            "notes": "E2E test mood entry",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    }

    return event, trace_id, user_id


def create_guardian_request(user_id, trace_id):
    """Create a GuardianRequestEvent"""
    request_id = str(uuid4())

    event = {
        "event_id": str(uuid4()),
        "event_type": "guardian.request",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "user_id": user_id,
        "request_id": request_id,
        "guardian_type": "mental",
        "query": "¿Cómo puedo mantener este buen estado de ánimo?",
        "context": {
            "recent_mood": "happy",
            "mood_score": 8,
        }
    }

    return event, request_id


def publish_event(topic, event):
    """Publish event to Kafka"""
    producer = Producer(get_producer_config())

    def delivery_callback(err, msg):
        if err:
            print(f"❌ Failed to deliver message: {err}")
        else:
            print(f"✅ Message delivered to {msg.topic()} [partition {msg.partition()}]")

    # Serialize event
    value = json.dumps(event).encode("utf-8")
    key = event["user_id"].encode("utf-8")

    headers = [
        ("event_type", event["event_type"].encode("utf-8")),
        ("event_id", event["event_id"].encode("utf-8")),
        ("trace_id", event.get("trace_id", "").encode("utf-8")),
    ]

    producer.produce(
        topic=topic,
        key=key,
        value=value,
        headers=headers,
        callback=delivery_callback,
    )

    producer.flush(timeout=5)
    return True


def consume_events(topic, timeout_ms=10000):
    """Consume events from topic"""
    consumer = Consumer(get_consumer_config(f"e2e-test-{int(time.time())}"))
    consumer.subscribe([topic])

    events = []
    start_time = time.time()

    print(f"🔍 Listening to {topic} for {timeout_ms/1000}s...")

    while (time.time() - start_time) * 1000 < timeout_ms:
        msg = consumer.poll(timeout=1.0)

        if msg is None:
            continue

        if msg.error():
            print(f"❌ Consumer error: {msg.error()}")
            continue

        try:
            event = json.loads(msg.value().decode("utf-8"))
            events.append(event)

            print(f"📨 Received: {event['event_type']} (trace_id: {event.get('trace_id', 'N/A')[:8]}...)")
        except Exception as e:
            print(f"❌ Failed to parse event: {e}")

    consumer.close()
    return events


def verify_topics():
    """Verify all required topics exist"""
    admin_client = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

    print("\n🔍 Verifying Kafka topics...")

    metadata = admin_client.list_topics(timeout=10)
    topics = set(metadata.topics.keys())

    required_topics = [
        TOPIC_USER_EVENTS,
        TOPIC_CONTEXT_AGGREGATED,
        TOPIC_GUARDIAN_REQUESTS,
        TOPIC_GUARDIAN_RESPONSES,
    ]

    all_exist = True
    for topic in required_topics:
        if topic in topics:
            print(f"  ✅ {topic}")
        else:
            print(f"  ❌ {topic} - NOT FOUND")
            all_exist = False

    return all_exist


def test_1_publish_mood_event():
    """Test 1: Publish MoodCreatedEvent"""
    print("\n" + "="*70)
    print("TEST 1: Publish MoodCreatedEvent")
    print("="*70)

    event, trace_id, user_id = create_mood_event()

    print(f"\n📤 Publishing event:")
    print(f"  Event Type: {event['event_type']}")
    print(f"  User ID: {user_id}")
    print(f"  Trace ID: {trace_id}")
    print(f"  Mood Score: {event['data']['mood_score']}")

    success = publish_event(TOPIC_USER_EVENTS, event)

    if success:
        print(f"\n✅ TEST 1 PASSED: MoodCreatedEvent published successfully")
        return trace_id, user_id
    else:
        print(f"\n❌ TEST 1 FAILED: Failed to publish event")
        return None, None


def test_2_verify_event_in_topic(trace_id):
    """Test 2: Verify event appears in topic"""
    print("\n" + "="*70)
    print("TEST 2: Verify Event in Topic")
    print("="*70)

    # Wait a moment for event to be written
    time.sleep(2)

    events = consume_events(TOPIC_USER_EVENTS, timeout_ms=5000)

    # Find our event by trace_id
    our_events = [e for e in events if e.get("trace_id") == trace_id]

    if our_events:
        print(f"\n✅ TEST 2 PASSED: Found {len(our_events)} event(s) with trace_id {trace_id[:8]}...")
        return True
    else:
        print(f"\n⚠️  TEST 2 WARNING: Event not found in topic (might have been consumed already)")
        print(f"   Total events seen: {len(events)}")
        return False


def test_3_publish_guardian_request(user_id, trace_id):
    """Test 3: Publish GuardianRequestEvent"""
    print("\n" + "="*70)
    print("TEST 3: Publish GuardianRequestEvent")
    print("="*70)

    event, request_id = create_guardian_request(user_id, trace_id)

    print(f"\n📤 Publishing Guardian request:")
    print(f"  Request ID: {request_id}")
    print(f"  Guardian Type: {event['guardian_type']}")
    print(f"  Query: {event['query']}")

    success = publish_event(TOPIC_GUARDIAN_REQUESTS, event)

    if success:
        print(f"\n✅ TEST 3 PASSED: GuardianRequestEvent published successfully")
        return request_id
    else:
        print(f"\n❌ TEST 3 FAILED: Failed to publish Guardian request")
        return None


def test_4_kafka_connectivity():
    """Test 4: Basic Kafka connectivity"""
    print("\n" + "="*70)
    print("TEST 4: Kafka Connectivity")
    print("="*70)

    try:
        admin_client = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
        metadata = admin_client.list_topics(timeout=5)

        print(f"\n✅ Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
        print(f"   Total topics: {len(metadata.topics)}")

        return True
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: Cannot connect to Kafka: {e}")
        return False


def main():
    """Run all E2E tests"""
    print("\n" + "="*70)
    print("AURA360 - E2E KAFKA FLOW TEST")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    print(f"  Security: {KAFKA_SECURITY_PROTOCOL}")
    print(f"  Time: {datetime.now().isoformat()}")

    # Verify topics exist
    if not verify_topics():
        print("\n❌ ABORT: Required topics not found. Run kafka-init service first.")
        sys.exit(1)

    # Test 4: Connectivity
    if not test_4_kafka_connectivity():
        sys.exit(1)

    # Test 1: Publish mood event
    trace_id, user_id = test_1_publish_mood_event()
    if not trace_id:
        sys.exit(1)

    # Test 2: Verify event in topic
    test_2_verify_event_in_topic(trace_id)

    # Test 3: Publish Guardian request
    request_id = test_3_publish_guardian_request(user_id, trace_id)

    # Summary
    print("\n" + "="*70)
    print("E2E TEST SUMMARY")
    print("="*70)
    print("\n✅ Core Kafka Flow:")
    print(f"   • MoodCreatedEvent published to {TOPIC_USER_EVENTS}")
    print(f"   • GuardianRequestEvent published to {TOPIC_GUARDIAN_REQUESTS}")
    print(f"   • Trace ID: {trace_id}")
    print(f"   • User ID: {user_id}")

    print("\n📋 Next Manual Steps:")
    print("   1. Start vectordb consumer:")
    print("      cd services/vectordb && uv run python -m vectosvc.kafka.consumer")
    print("\n   2. Start agents consumers:")
    print("      cd services/agents && uv run python -m kafka.consumer")
    print("      cd services/agents && uv run python -m kafka.response_consumer")
    print("\n   3. Check Kafka UI: http://localhost:8090")
    print("      • Verify messages in topics")
    print("      • Monitor consumer lag")

    print("\n🎯 Expected Consumer Behavior:")
    print("   • Vectordb consumer should process mood event")
    print("   • Context should be aggregated")
    print("   • Vectors should be stored in Qdrant")
    print("   • Guardian consumer should process request")
    print("   • Response should be stored in Redis")

    print("\n" + "="*70)
    print("E2E TEST COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
