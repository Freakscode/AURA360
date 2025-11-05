"""
Pruebas de integración para el servicio vectorial (vectosvc).

Valida:
- Endpoints de salud y métricas
- Ingesta de documentos (sync y batch)
- Búsqueda semántica básica
- Búsqueda con filtros de categoría y metadatos
- Endpoints del DLQ (Dead Letter Queue)
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import pytest
import requests
from requests.exceptions import ConnectionError, Timeout


VECTORIAL_SERVICE_URL = "http://localhost:8001"
TEST_TIMEOUT = 30


@pytest.fixture(scope="module")
def service_url() -> str:
    """URL base del servicio vectorial."""
    return VECTORIAL_SERVICE_URL


@pytest.fixture(scope="module")
def wait_for_service(service_url: str) -> None:
    """Espera a que el servicio vectorial esté disponible."""
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{service_url}/readyz", timeout=5)
            if response.status_code == 200:
                return
        except (ConnectionError, Timeout):
            pass
        
        if attempt < max_attempts - 1:
            time.sleep(2)
    
    pytest.fail(
        f"El servicio vectorial no está disponible en {service_url}. "
        f"Asegúrate de ejecutar: cd vectorial_db && docker compose up -d"
    )


@pytest.fixture(scope="module")
def trace_id() -> str:
    """Genera un trace_id único para este módulo de pruebas."""
    return f"test-vectorial-{uuid.uuid4()}"


class TestHealthAndMetrics:
    """Pruebas de salud y métricas del servicio."""

    def test_health_check(self, service_url: str, wait_for_service: None) -> None:
        """Valida que el endpoint de salud responde correctamente."""
        response = requests.get(f"{service_url}/readyz", timeout=5)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_metrics_endpoint(self, service_url: str, wait_for_service: None) -> None:
        """Valida que el endpoint de métricas retorna información del sistema."""
        response = requests.get(f"{service_url}/metrics", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar estructura de métricas
        assert "service" in data
        assert data["service"]["name"] == "vectosvc"
        assert "version" in data["service"]
        assert "uptime_seconds" in data["service"]
        
        assert "collection" in data
        assert "name" in data["collection"]
        assert "total_points" in data["collection"]
        assert "vector_size" in data["collection"]
        
        assert "cache" in data
        assert "pipeline" in data
        assert "config" in data


class TestIngestion:
    """Pruebas de ingesta de documentos."""

    def test_ingest_single_document(
        self,
        service_url: str,
        wait_for_service: None,
        trace_id: str,
    ) -> None:
        """Valida la ingesta de un documento individual."""
        doc_id = f"test-doc-{uuid.uuid4()}"
        payload = {
            "doc_id": doc_id,
            "text": "La meditación mindfulness mejora la salud mental y reduce el estrés.",
            "metadata": {
                "category": "mind",
                "source": "test",
                "trace_id": trace_id,
            },
        }
        
        response = requests.post(
            f"{service_url}/ingest",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        
        # Esperar a que el job se procese
        job_id = data["job_id"]
        _wait_for_job_completion(service_url, job_id)

    def test_ingest_batch_documents(
        self,
        service_url: str,
        wait_for_service: None,
        trace_id: str,
    ) -> None:
        """Valida la ingesta de múltiples documentos en batch."""
        batch_payload = [
            {
                "doc_id": f"test-batch-doc-{i}-{uuid.uuid4()}",
                "text": f"Documento de prueba #{i} sobre {category}.",
                "metadata": {
                    "category": category,
                    "source": "test_batch",
                    "trace_id": trace_id,
                    "index": i,
                },
            }
            for i, category in enumerate(["mind", "body", "soul"], start=1)
        ]
        
        response = requests.post(
            f"{service_url}/ingest/batch",
            json=batch_payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 202
        data = response.json()
        assert "job_ids" in data
        assert data["status"] == "queued"
        assert len(data["job_ids"]) == len(batch_payload)
        
        # Esperar a que todos los jobs se procesen
        for job_id in data["job_ids"]:
            _wait_for_job_completion(service_url, job_id)


class TestSearch:
    """Pruebas de búsqueda semántica."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, service_url: str, trace_id: str) -> None:
        """Crea datos de prueba antes de cada test de búsqueda."""
        test_docs = [
            {
                "doc_id": f"search-test-mind-{uuid.uuid4()}",
                "text": "La respiración consciente es una técnica efectiva para reducir el estrés y mejorar el enfoque mental.",
                "metadata": {
                    "category": "mind",
                    "source": "test_search",
                    "trace_id": trace_id,
                    "topic": "mindfulness",
                },
            },
            {
                "doc_id": f"search-test-body-{uuid.uuid4()}",
                "text": "El ejercicio cardiovascular regular mejora la salud del corazón y aumenta la resistencia física.",
                "metadata": {
                    "category": "body",
                    "source": "test_search",
                    "trace_id": trace_id,
                    "topic": "cardio",
                },
            },
            {
                "doc_id": f"search-test-soul-{uuid.uuid4()}",
                "text": "La práctica diaria de gratitud fortalece el bienestar espiritual y la conexión con el propósito personal.",
                "metadata": {
                    "category": "soul",
                    "source": "test_search",
                    "trace_id": trace_id,
                    "topic": "gratitude",
                },
            },
        ]
        
        # Ingestar documentos
        response = requests.post(
            f"{service_url}/ingest/batch",
            json=test_docs,
            timeout=TEST_TIMEOUT,
        )
        assert response.status_code == 202
        
        # Esperar a que se completen los jobs
        job_ids = response.json()["job_ids"]
        for job_id in job_ids:
            _wait_for_job_completion(service_url, job_id)
        
        # Esperar a que Qdrant indexe los documentos
        time.sleep(2)

    def test_basic_search(self, service_url: str, wait_for_service: None) -> None:
        """Valida la búsqueda semántica básica."""
        payload = {
            "query": "técnicas de respiración",
            "limit": 5,
        }
        
        response = requests.post(
            f"{service_url}/search",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "hits" in data
        assert isinstance(data["hits"], list)
        
        if data["hits"]:
            hit = data["hits"][0]
            assert "id" in hit
            assert "score" in hit
            assert "payload" in hit

    def test_search_with_category_filter(
        self,
        service_url: str,
        wait_for_service: None,
    ) -> None:
        """Valida la búsqueda con filtro de categoría."""
        payload = {
            "query": "mejorar salud",
            "limit": 10,
            "filter": {
                "must": {"category": "body"}
            },
        }
        
        response = requests.post(
            f"{service_url}/search",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "hits" in data
        
        # Validar que todos los resultados sean de la categoría 'body'
        for hit in data["hits"]:
            if "payload" in hit and "category" in hit["payload"]:
                assert hit["payload"]["category"] == "body"


class TestDLQ:
    """Pruebas del Dead Letter Queue (DLQ)."""

    def test_dlq_stats_endpoint(self, service_url: str, wait_for_service: None) -> None:
        """Valida que el endpoint de estadísticas del DLQ responde."""
        response = requests.get(f"{service_url}/dlq/stats", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar estructura básica de estadísticas
        assert "total_failures" in data
        assert isinstance(data["total_failures"], int)

    def test_dlq_list_endpoint(self, service_url: str, wait_for_service: None) -> None:
        """Valida que el endpoint de listado del DLQ responde."""
        response = requests.get(
            f"{service_url}/dlq",
            params={"limit": 10, "offset": 0},
            timeout=10,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "entries" in data
        assert "stats" in data
        assert isinstance(data["entries"], list)


# Funciones auxiliares

def _wait_for_job_completion(
    service_url: str,
    job_id: str,
    max_wait_seconds: int = 30,
) -> dict[str, Any]:
    """Espera a que un job de ingesta se complete."""
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        try:
            response = requests.get(f"{service_url}/jobs/{job_id}", timeout=5)
            if response.status_code == 200:
                job = response.json()
                status = job.get("status")
                
                if status in {"completed", "failed"}:
                    if status == "failed":
                        pytest.fail(f"Job {job_id} falló: {job.get('error')}")
                    return job
        except (ConnectionError, Timeout):
            pass
        
        time.sleep(1)
    
    pytest.fail(f"Job {job_id} no se completó en {max_wait_seconds} segundos")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

