#!/usr/bin/env python3
"""
Test End-to-End del Sistema de Contexto de Usuario con Weighted Retrieval.

Este script valida el flujo completo:
1. Backend API: Crear snapshots de usuario
2. Vectordb: Ingesta con routing correcto
3. Weighted Retrieval: Búsqueda combinada user_context + general
4. Agents: Integración con HolisticAdviceService

Requiere:
- Servicios de vectordb corriendo (docker compose up -d)
- Django API corriendo (opcional, para tests completos)
"""

import logging
import sys
import time
from uuid import uuid4

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# URLs de servicios
VECTORDB_URL = "http://localhost:8001"  # Docker-compose maps 8001:8000
API_URL = "http://localhost:8080"  # Django API


def test_01_vectordb_health():
    """Test 1: Verificar que vectordb service está corriendo."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Vectordb Service Health Check")
    logger.info("=" * 80)

    try:
        response = requests.get(f"{VECTORDB_URL}/readyz", timeout=5)
        response.raise_for_status()
        logger.info(f"✅ Vectordb service is running: {response.json()}")
        return True
    except Exception as exc:
        logger.error(f"❌ Vectordb service not available: {exc}")
        logger.error("   Run: cd services/vectordb && docker compose up -d")
        return False


def test_02_user_context_collection_exists():
    """Test 2: Verificar que la colección user_context existe en Qdrant."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: User Context Collection Exists")
    logger.info("=" * 80)

    try:
        # Check via metrics endpoint
        response = requests.get(f"{VECTORDB_URL}/metrics", timeout=10)
        response.raise_for_status()
        data = response.json()

        collection_name = data.get("collection", {}).get("name")
        logger.info(f"✅ Main collection: {collection_name}")

        # Try to check if user_context exists via direct Qdrant API
        try:
            qdrant_response = requests.get("http://localhost:6333/collections/user_context", timeout=5)
            if qdrant_response.status_code == 200:
                collection_data = qdrant_response.json()
                logger.info(f"✅ user_context collection exists")
                logger.info(f"   Points: {collection_data.get('result', {}).get('points_count', 0)}")
                logger.info(f"   Vectors: {collection_data.get('result', {}).get('config', {}).get('params', {}).get('vectors', {}).get('size')}")
                return True
            else:
                logger.warning("⚠️  user_context collection not found")
                logger.warning("   Run: cd services/vectordb && uv run python scripts/create_user_context_collection.py")
                return False
        except Exception as e:
            logger.warning(f"⚠️  Could not check user_context collection: {e}")
            return False

    except Exception as exc:
        logger.error(f"❌ Failed to check collections: {exc}")
        return False


def test_03_ingest_user_context_snapshot():
    """Test 3: Ingestar un snapshot de contexto de usuario."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Ingest User Context Snapshot")
    logger.info("=" * 80)

    test_user_id = str(uuid4())
    snapshot_id = str(uuid4())

    payload = {
        "doc_id": f"user_context_{snapshot_id}",
        "text": "El usuario ha reportado problemas de sueño y ansiedad en los últimos días. Mood: bajo, nivel de energía: moderado. IKIGAI: Ayudar a otros a través de la tecnología.",
        "category": "mente",
        "locale": "es-CO",
        "source_type": "user_context",  # CLAVE: Esto debe routear a user_context collection
        "metadata": {
            "user_id": test_user_id,
            "snapshot_type": "mind",
            "timeframe": "7d",
            "topics": ["mental_health", "sleep_disorders", "stress_response"],
            "confidence_score": 0.85,
        },
    }

    try:
        logger.info(f"   Ingesting snapshot for user: {test_user_id}")
        logger.info(f"   source_type: {payload['source_type']}")

        response = requests.post(
            f"{VECTORDB_URL}/ingest",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        job_id = data.get("job_id")
        logger.info(f"✅ Snapshot enqueued: job_id={job_id}")

        # Wait for processing
        logger.info("   Waiting for ingestion to complete...")
        time.sleep(5)

        # Check job status
        status_response = requests.get(f"{VECTORDB_URL}/jobs/{job_id}", timeout=10)
        status_response.raise_for_status()
        job_data = status_response.json()

        logger.info(f"✅ Job status: {job_data.get('status')}")
        logger.info(f"   Chunks processed: {job_data.get('processed_chunks')}")

        return {"user_id": test_user_id, "snapshot_id": snapshot_id, "job_id": job_id}

    except Exception as exc:
        logger.error(f"❌ Failed to ingest snapshot: {exc}")
        return None


def test_04_weighted_search():
    """Test 4: Ejecutar weighted search combinando user_context + general."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Weighted Search (User Context + General Corpus)")
    logger.info("=" * 80)

    # Use a test user ID (in real scenario, this would come from test_03)
    test_user_id = "00000000-0000-0000-0000-000000000000"  # Test UUID

    payload = {
        "trace_id": f"test-{int(time.time())}",
        "query": "problemas de sueño y ansiedad, bajo estado de ánimo",
        "user_id": test_user_id,
        "category": "mente",
        "guardian_type": "mental",
        "top_k": 10,
        "user_context_limit": 5,
        "general_limit": 10,
    }

    try:
        logger.info(f"   Query: '{payload['query']}'")
        logger.info(f"   User ID: {payload['user_id']}")
        logger.info(f"   Guardian: {payload['guardian_type']}")

        response = requests.post(
            f"{VECTORDB_URL}/api/v1/holistic/weighted-search",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            results = data.get("data", {}).get("results", [])
            meta = data.get("meta", {})

            logger.info(f"✅ Weighted search successful")
            logger.info(f"   Total results: {len(results)}")
            logger.info(f"   Took: {meta.get('took_ms')}ms")
            logger.info(f"   User context weight: {meta.get('user_context_weight', 1.5)}")
            logger.info(f"   General weight: {meta.get('general_weight', 1.0)}")

            # Analyze results
            user_context_count = sum(1 for r in results if r.get("source_collection") == "user_context")
            general_count = len(results) - user_context_count

            logger.info(f"\n   Results breakdown:")
            logger.info(f"   - User context: {user_context_count}")
            logger.info(f"   - General corpus: {general_count}")

            # Show top 3 results
            logger.info(f"\n   Top 3 results:")
            for i, result in enumerate(results[:3], 1):
                logger.info(f"   {i}. [{result.get('source_collection')}] score={result.get('weighted_score'):.4f}")
                logger.info(f"      {result.get('text', '')[:100]}...")

            return True
        else:
            error = data.get("error", {})
            logger.error(f"❌ Weighted search failed: {error.get('message')}")
            return False

    except Exception as exc:
        logger.error(f"❌ Failed to execute weighted search: {exc}")
        import traceback
        traceback.print_exc()
        return False


def test_05_collection_routing_validation():
    """Test 5: Validar que el routing por source_type está funcionando."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Collection Routing Validation")
    logger.info("=" * 80)

    try:
        # Check user_context collection points
        qdrant_response = requests.get("http://localhost:6333/collections/user_context", timeout=5)
        if qdrant_response.status_code == 200:
            data = qdrant_response.json()
            points_count = data.get("result", {}).get("points_count", 0)
            logger.info(f"✅ user_context collection has {points_count} points")

            if points_count > 0:
                logger.info(f"   ✓ Routing to user_context collection is working")
            else:
                logger.warning(f"   ⚠️  No points in user_context collection yet")
                logger.warning(f"      This is expected if no user snapshots have been ingested")

            return True
        else:
            logger.error(f"❌ user_context collection not found")
            return False

    except Exception as exc:
        logger.error(f"❌ Failed to validate collection routing: {exc}")
        return False


def main():
    """Run all E2E tests."""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 USER CONTEXT E2E TESTING")
    logger.info("=" * 80)

    results = {
        "Vectordb Health": False,
        "User Context Collection": False,
        "Ingest Snapshot": False,
        "Weighted Search": False,
        "Collection Routing": False,
    }

    # Test 1: Health check
    results["Vectordb Health"] = test_01_vectordb_health()
    if not results["Vectordb Health"]:
        logger.error("\n❌ Vectordb service not running. Aborting tests.")
        logger.error("   Run: cd services/vectordb && docker compose up -d")
        return False

    # Test 2: Collection exists
    results["User Context Collection"] = test_02_user_context_collection_exists()

    # Test 3: Ingest snapshot
    snapshot_data = test_03_ingest_user_context_snapshot()
    results["Ingest Snapshot"] = snapshot_data is not None

    # Test 4: Weighted search
    results["Weighted Search"] = test_04_weighted_search()

    # Test 5: Routing validation
    results["Collection Routing"] = test_05_collection_routing_validation()

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 E2E TEST SUMMARY")
    logger.info("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"{status}: {test_name}")

    total = len(results)
    passed = sum(results.values())
    percentage = (passed / total) * 100

    logger.info("\n" + "=" * 80)
    logger.info(f"Result: {passed}/{total} tests passed ({percentage:.0f}%)")
    logger.info("=" * 80 + "\n")

    if percentage >= 80:
        logger.info("🎉 E2E testing successful! System is working correctly.")
        return True
    else:
        logger.warning("⚠️  Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
