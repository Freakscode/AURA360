"""
Pruebas de integración para el servicio de agentes (agents-service).

Valida:
- Conexión con el servicio vectorial (Qdrant)
- Generación de recomendaciones por categoría (mind, body, soul, holistic)
- Manejo de errores (categoría no soportada, timeout vectorial, etc.)
- Estructura de respuesta y metadatos
- Latencia y performance básico

Prerequisitos:
- Servicio vectorial debe estar corriendo (docker compose up -d en vectorial_db/)
- Variable GOOGLE_API_KEY debe estar configurada
- Colección 'holistic_agents' debe existir en Qdrant
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import pytest
import requests
from requests.exceptions import ConnectionError, Timeout


AGENTS_SERVICE_URL = "http://localhost:8080"
VECTORIAL_SERVICE_URL = "http://localhost:8001"
TEST_TIMEOUT = 120  # Los agentes pueden tardar más


@pytest.fixture(scope="module")
def service_url() -> str:
    """URL base del servicio de agentes."""
    return AGENTS_SERVICE_URL


@pytest.fixture(scope="module")
def wait_for_services() -> None:
    """Espera a que todos los servicios requeridos estén disponibles."""
    # Verificar servicio vectorial
    _wait_for_service(
        VECTORIAL_SERVICE_URL,
        "/readyz",
        "servicio vectorial",
        "cd vectorial_db && docker compose up -d",
    )
    
    # Verificar servicio de agentes
    _wait_for_service(
        AGENTS_SERVICE_URL,
        "/readyz",
        "servicio de agentes",
        "cd agents-service && uv run uvicorn main:app --reload --port 8080",
    )


@pytest.fixture(scope="module")
def trace_id() -> str:
    """Genera un trace_id único para este módulo de pruebas."""
    return f"test-agents-{uuid.uuid4()}"


@pytest.fixture(scope="module")
def test_user_profile() -> dict[str, Any]:
    """Perfil de usuario de prueba."""
    return {
        "id": f"test-user-{uuid.uuid4()}",
        "name": "Usuario de Prueba",
        "age": 30,
        "locale": "es-CO",
        "goals": ["reducir estrés", "mejorar salud"],
    }


class TestAdviceEndpoint:
    """Pruebas del endpoint principal de recomendaciones."""

    @pytest.mark.parametrize(
        "category,expected_dimension",
        [
            ("mind", "mente"),
            ("body", "cuerpo"),
            ("soul", "alma"),
            ("holistic", "integral"),
        ],
    )
    def test_generate_advice_by_category(
        self,
        service_url: str,
        wait_for_services: None,
        trace_id: str,
        test_user_profile: dict[str, Any],
        category: str,
        expected_dimension: str,
    ) -> None:
        """Valida la generación de recomendaciones para cada categoría."""
        payload = {
            "trace_id": f"{trace_id}-{category}",
            "category": category,
            "user_profile": test_user_profile,
            "preferences": {
                "focus": ["bienestar"],
                "intensity_level": "medium",
            },
            "context": f"Necesito recomendaciones para mejorar mi {expected_dimension}.",
        }
        
        response = requests.post(
            f"{service_url}/api/v1/holistic/advice",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar estructura de respuesta
        assert data["status"] == "success"
        assert "data" in data
        assert "error" in data
        assert data["error"] is None
        assert "meta" in data
        
        # Validar metadatos
        assert data["meta"]["trace_id"] == payload["trace_id"]
        assert "model_version" in data["meta"]
        assert "timestamp" in data["meta"]
        
        # Validar datos de respuesta
        response_data = data["data"]
        assert "summary" in response_data
        assert "recommendations" in response_data
        assert "agent_runs" in response_data
        
        # Validar recomendaciones
        recommendations = response_data["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert "title" in rec
            assert "description" in rec
            assert "dimension" in rec
            assert rec["dimension"] == expected_dimension
            assert "confidence" in rec
            assert "metadata" in rec

    def test_advice_with_spanish_category_aliases(
        self,
        service_url: str,
        wait_for_services: None,
        trace_id: str,
        test_user_profile: dict[str, Any],
    ) -> None:
        """Valida que los aliases en español funcionan correctamente."""
        spanish_categories = ["mente", "cuerpo", "alma", "holistico"]
        
        for category in spanish_categories:
            payload = {
                "trace_id": f"{trace_id}-{category}",
                "category": category,
                "user_profile": test_user_profile,
            }
            
            response = requests.post(
                f"{service_url}/api/v1/holistic/advice",
                json=payload,
                timeout=TEST_TIMEOUT,
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_advice_includes_vector_query_info(
        self,
        service_url: str,
        wait_for_services: None,
        trace_id: str,
        test_user_profile: dict[str, Any],
    ) -> None:
        """Valida que la respuesta incluye información de las consultas vectoriales."""
        payload = {
            "trace_id": f"{trace_id}-vector-info",
            "category": "mind",
            "user_profile": test_user_profile,
            "context": "Necesito técnicas de meditación para principiantes.",
        }
        
        response = requests.post(
            f"{service_url}/api/v1/holistic/advice",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar que hay información de agent runs
        agent_runs = data["data"]["agent_runs"]
        assert len(agent_runs) > 0
        
        first_run = agent_runs[0]
        assert "agent_name" in first_run
        assert "status" in first_run
        assert first_run["status"] == "completed"
        assert "latency_ms" in first_run
        assert "input_context" in first_run
        assert "output_payload" in first_run
        assert "vector_queries" in first_run
        
        # Validar estructura de vector_queries
        vector_queries = first_run["vector_queries"]
        assert isinstance(vector_queries, list)
        
        # Si hay consultas vectoriales, validar su estructura
        if vector_queries:
            query = vector_queries[0]
            assert "vector_store" in query
            assert "embedding_model" in query
            assert "query_text" in query
            assert "top_k" in query


class TestErrorHandling:
    """Pruebas de manejo de errores."""

    def test_unsupported_category_returns_422(
        self,
        service_url: str,
        wait_for_services: None,
        trace_id: str,
        test_user_profile: dict[str, Any],
    ) -> None:
        """Valida que categorías no soportadas retornan error 422."""
        payload = {
            "trace_id": f"{trace_id}-unsupported",
            "category": "invalid_category",
            "user_profile": test_user_profile,
        }
        
        response = requests.post(
            f"{service_url}/api/v1/holistic/advice",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"
        assert data["error"]["type"] == "unsupported_category"

    def test_missing_required_fields_returns_422(
        self,
        service_url: str,
        wait_for_services: None,
    ) -> None:
        """Valida que faltan campos obligatorios retornan error 422."""
        # Sin trace_id
        payload = {
            "category": "mind",
            "user_profile": {"id": "test"},
        }
        
        response = requests.post(
            f"{service_url}/api/v1/holistic/advice",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 422

    def test_empty_user_profile_returns_422(
        self,
        service_url: str,
        wait_for_services: None,
        trace_id: str,
    ) -> None:
        """Valida que un perfil vacío retorna error 422."""
        payload = {
            "trace_id": f"{trace_id}-empty-profile",
            "category": "mind",
            "user_profile": {},
        }
        
        response = requests.post(
            f"{service_url}/api/v1/holistic/advice",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        
        assert response.status_code == 422


class TestPerformance:
    """Pruebas básicas de performance."""

    def test_advice_latency_is_reasonable(
        self,
        service_url: str,
        wait_for_services: None,
        trace_id: str,
        test_user_profile: dict[str, Any],
    ) -> None:
        """Valida que la latencia de generación es razonable."""
        payload = {
            "trace_id": f"{trace_id}-latency",
            "category": "mind",
            "user_profile": test_user_profile,
            "context": "Técnicas rápidas de relajación.",
        }
        
        start = time.perf_counter()
        response = requests.post(
            f"{service_url}/api/v1/holistic/advice",
            json=payload,
            timeout=TEST_TIMEOUT,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar que la latencia reportada está presente
        agent_runs = data["data"]["agent_runs"]
        assert len(agent_runs) > 0
        reported_latency = agent_runs[0]["latency_ms"]
        assert reported_latency > 0
        
        # La latencia total (incluyendo red) debe ser razonable
        # Nota: Los LLMs pueden tardar varios segundos
        assert elapsed_ms < 60000  # Menos de 60 segundos


# Funciones auxiliares

def _wait_for_service(
    base_url: str,
    health_path: str,
    service_name: str,
    start_command: str,
    max_attempts: int = 30,
) -> None:
    """Espera a que un servicio esté disponible."""
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}{health_path}", timeout=5)
            if response.status_code == 200:
                return
        except (ConnectionError, Timeout):
            pass
        
        if attempt < max_attempts - 1:
            time.sleep(2)
    
    pytest.fail(
        f"El {service_name} no está disponible en {base_url}. "
        f"Asegúrate de ejecutar: {start_command}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

