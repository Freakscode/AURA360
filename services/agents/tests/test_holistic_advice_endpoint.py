from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient

from agents_service.api.dependencies import get_holistic_service
from infra.env import load_environment
from infra.settings import get_settings
from main import app
from services.exceptions import UnsupportedCategoryError, VectorQueryError


@pytest.fixture()
def client() -> tuple[TestClient, Callable[[], None]]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _override_service(service: Any) -> None:
    app.dependency_overrides[get_holistic_service] = lambda: service


class _BaseStubService:
    def __init__(self) -> None:
        load_environment(override=False)
        self.settings = get_settings()


class _SuccessStubService(_BaseStubService):
    def generate_advice(self, request) -> dict[str, Any]:  # type: ignore[override]
        timestamp = datetime.now(timezone.utc).isoformat()
        return {
            "status": "success",
            "data": {
                "summary": "Plan personalizado generado correctamente.",
                "recommendations": [
                    {
                        "title": "Acción 1",
                        "description": "Realiza respiración consciente 5 minutos al día.",
                        "dimension": "mente",
                        "confidence": 0.87,
                        "metadata": {"source": "demo"},
                    }
                ],
                "agent_runs": [
                    {
                        "agent_name": "mental_guardian",
                        "status": "completed",
                        "latency_ms": 123,
                        "input_context": {"category": request.category},
                        "output_payload": {"message": "ok"},
                        "vector_queries": [
                            {
                                "vector_store": "qdrant",
                                "embedding_model": "text-embedding-3-small",
                                "query_text": "contexto base",
                                "top_k": 5,
                                "response_payload": {"hits": []},
                                "confidence_score": 0.87,
                            }
                        ],
                    }
                ],
            },
            "error": None,
            "meta": {
                "trace_id": request.trace_id,
                "model_version": self.settings.model_version,
                "timestamp": timestamp,
            },
        }


class _UnsupportedStubService(_BaseStubService):
    def generate_advice(self, request) -> dict[str, Any]:  # type: ignore[override]
        raise UnsupportedCategoryError(category=request.category)


class _VectorErrorStubService(_BaseStubService):
    def generate_advice(self, request) -> dict[str, Any]:  # type: ignore[override]
        raise VectorQueryError(
            message="Timeout consultando Qdrant",
            details={"retry_count": 2},
        )


@pytest.mark.parametrize(
    "category",
    ["mind", "Mind", "MENTE"],
)
def test_success_response_with_vector_queries(category: str, client: TestClient) -> None:
    service = _SuccessStubService()
    _override_service(service)

    payload = {
        "trace_id": "trace-success-123",
        "category": category,
        "user_profile": {"id": "user-1", "name": "Rene", "locale": "es-CO"},
        "preferences": {"focus": ["respiración"]},
        "context": "Necesito recomendaciones para manejar el estrés.",
    }

    response = client.post("/api/v1/holistic/advice", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["data"]["summary"]
    assert body["data"]["recommendations"][0]["dimension"] == "mente"
    vector_info = body["data"]["agent_runs"][0]["vector_queries"][0]
    assert vector_info["vector_store"] == "qdrant"
    assert body["meta"]["trace_id"] == payload["trace_id"]


def test_unsupported_category_returns_422(client: TestClient) -> None:
    service = _UnsupportedStubService()
    _override_service(service)

    payload = {
        "trace_id": "trace-unsupported",
        "category": "unknown",
        "user_profile": {"id": "user-1"},
    }

    response = client.post("/api/v1/holistic/advice", json=payload)
    body = response.json()

    assert response.status_code == 422
    assert body["status"] == "error"
    assert body["error"]["type"] == "unsupported_category"
    assert body["meta"]["trace_id"] == payload["trace_id"]


def test_vector_service_timeout_returns_502(client: TestClient) -> None:
    service = _VectorErrorStubService()
    _override_service(service)

    payload = {
        "trace_id": "trace-vector-fail",
        "category": "mind",
        "user_profile": {"id": "user-1"},
    }

    response = client.post("/api/v1/holistic/advice", json=payload)
    body = response.json()

    assert response.status_code == 502
    assert body["status"] == "error"
    assert body["error"]["type"] == "vector_query_error"
    assert body["meta"]["trace_id"] == payload["trace_id"]