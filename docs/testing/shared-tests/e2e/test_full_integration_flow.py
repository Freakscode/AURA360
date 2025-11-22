"""
Pruebas End-to-End del flujo completo de AURA360.

Este conjunto de pruebas valida la integración completa de:
1. Ingesta de documentos → Servicio Vectorial
2. Cliente → Backend Django
3. Backend → Servicio de Agentes
4. Servicio de Agentes → Servicio Vectorial (búsqueda)
5. Respuesta completa hasta el cliente

Prerequisitos:
- Servicio vectorial corriendo (docker compose up -d en vectorial_db/)
- Servicio de agentes corriendo (uvicorn main:app --port 8080 en agents-service/)
- Backend Django corriendo (python manage.py runserver en backend/)
- Base de datos configurada y migrada
- Variables de entorno configuradas correctamente
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import pytest
import requests
from requests.exceptions import ConnectionError, Timeout


# URLs de servicios
BACKEND_URL = "http://localhost:8000"
AGENTS_SERVICE_URL = "http://localhost:8080"
VECTORIAL_SERVICE_URL = "http://localhost:8001"

# Timeouts
SERVICE_TIMEOUT = 5
REQUEST_TIMEOUT = 120


class ServiceChecker:
    """Utilidad para verificar disponibilidad de servicios."""
    
    @staticmethod
    def is_available(url: str, path: str = "/readyz", timeout: int = SERVICE_TIMEOUT) -> bool:
        """Verifica si un servicio está disponible."""
        try:
            response = requests.get(f"{url}{path}", timeout=timeout)
            return response.status_code == 200
        except (ConnectionError, Timeout):
            return False
    
    @staticmethod
    def wait_for_service(
        url: str,
        name: str,
        path: str = "/readyz",
        max_attempts: int = 30,
    ) -> None:
        """Espera a que un servicio esté disponible."""
        for attempt in range(max_attempts):
            if ServiceChecker.is_available(url, path):
                return
            if attempt < max_attempts - 1:
                time.sleep(2)
        
        pytest.skip(f"El {name} no está disponible en {url}")


@pytest.fixture(scope="module")
def verify_all_services() -> None:
    """Verifica que todos los servicios requeridos estén disponibles."""
    services = [
        (VECTORIAL_SERVICE_URL, "servicio vectorial", "/readyz"),
        (AGENTS_SERVICE_URL, "servicio de agentes", "/readyz"),
        (BACKEND_URL, "backend Django", "/api/health"),  # Ajustar según tu endpoint
    ]
    
    for url, name, path in services:
        ServiceChecker.wait_for_service(url, name, path)


@pytest.fixture(scope="module")
def test_trace_id() -> str:
    """Genera un trace_id único para este conjunto de pruebas."""
    return f"e2e-test-{uuid.uuid4()}"


@pytest.fixture(scope="module")
def auth_token() -> str:
    """
    Obtiene un token de autenticación para el backend.
    
    Ajusta esta función según tu mecanismo de autenticación:
    - JWT
    - Token de Supabase
    - Session-based auth
    """
    # TODO: Implementar obtención de token según tu sistema de auth
    # Por ahora retornamos un token de prueba
    return "test-token-replace-with-real-auth"


@pytest.fixture(scope="module")
def test_user_id(auth_token: str) -> str:
    """
    Obtiene o crea un usuario de prueba y retorna su ID.
    
    Ajusta según tu implementación de usuarios.
    """
    # TODO: Crear o obtener usuario de prueba
    return f"test-user-{uuid.uuid4()}"


@pytest.fixture(scope="module")
def ingest_test_documents(
    verify_all_services: None,
    test_trace_id: str,
) -> list[dict[str, Any]]:
    """
    Ingesta documentos de prueba en el servicio vectorial.
    Retorna la lista de documentos ingestados.
    """
    documents = [
        {
            "doc_id": f"{test_trace_id}-mind-meditation",
            "text": "La meditación mindfulness es una práctica que mejora la concentración y reduce el estrés. "
                    "Se recomienda practicar 10-20 minutos diarios en un espacio tranquilo. "
                    "Beneficios incluyen mayor claridad mental, reducción de ansiedad y mejor regulación emocional.",
            "metadata": {
                "category": "mind",
                "source": "e2e_test",
                "topic": "meditation",
                "language": "es",
                "trace_id": test_trace_id,
            },
        },
        {
            "doc_id": f"{test_trace_id}-body-exercise",
            "text": "El ejercicio aeróbico regular fortalece el sistema cardiovascular y mejora la resistencia. "
                    "Se recomienda al menos 150 minutos de actividad moderada por semana. "
                    "Actividades como caminar, nadar o andar en bicicleta son excelentes opciones.",
            "metadata": {
                "category": "body",
                "source": "e2e_test",
                "topic": "exercise",
                "language": "es",
                "trace_id": test_trace_id,
            },
        },
        {
            "doc_id": f"{test_trace_id}-soul-gratitude",
            "text": "La práctica diaria de gratitud fortalece el bienestar espiritual y la conexión con el propósito. "
                    "Mantener un diario de gratitud y reconocer tres cosas positivas cada día "
                    "aumenta la satisfacción vital y reduce síntomas depresivos.",
            "metadata": {
                "category": "soul",
                "source": "e2e_test",
                "topic": "gratitude",
                "language": "es",
                "trace_id": test_trace_id,
            },
        },
    ]
    
    # Ingestar documentos
    response = requests.post(
        f"{VECTORIAL_SERVICE_URL}/ingest/batch",
        json=documents,
        timeout=REQUEST_TIMEOUT,
    )
    assert response.status_code == 202
    
    # Esperar a que se procesen
    job_ids = response.json()["job_ids"]
    for job_id in job_ids:
        _wait_for_job_completion(job_id, VECTORIAL_SERVICE_URL)
    
    # Esperar a que Qdrant indexe
    time.sleep(3)
    
    return documents


class TestE2EFullFlow:
    """Pruebas End-to-End del flujo completo."""

    def test_complete_advice_flow_mind_category(
        self,
        verify_all_services: None,
        ingest_test_documents: list[dict[str, Any]],
        auth_token: str,
        test_user_id: str,
        test_trace_id: str,
    ) -> None:
        """
        Flujo completo: Cliente → Backend → Agentes → Vector Search → Respuesta.
        Categoría: mind (mente).
        """
        # 1. Cliente envía solicitud al backend
        request_payload = {
            "user_id": test_user_id,
            "category": "mind",
            "metadata": {
                "context": "Me siento estresado por el trabajo y necesito técnicas de relajación.",
                "urgency": "medium",
            },
        }
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        start_time = time.perf_counter()
        response = requests.post(
            f"{BACKEND_URL}/api/v1/holistic/advice",
            json=request_payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        total_latency_ms = (time.perf_counter() - start_time) * 1000
        
        # 2. Validar respuesta del backend
        assert response.status_code in [200, 201]
        data = response.json()
        
        assert "trace_id" in data
        assert "status" in data
        assert data["status"] == "completed"
        
        # 3. Validar estructura de resultado
        result = data["result"]
        assert "summary" in result
        assert "recommendations" in result
        assert "agent_runs" in result
        
        # 4. Validar recomendaciones
        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        
        for rec in recommendations:
            assert "title" in rec
            assert "description" in rec
            assert "dimension" in rec
            assert rec["dimension"] == "mente"
        
        # 5. Validar que se usó búsqueda vectorial
        agent_runs = result["agent_runs"]
        assert len(agent_runs) > 0
        
        first_run = agent_runs[0]
        assert "vector_queries" in first_run
        
        # 6. Validar latencia razonable
        assert total_latency_ms < 120000  # Menos de 2 minutos

    def test_complete_advice_flow_holistic_category(
        self,
        verify_all_services: None,
        ingest_test_documents: list[dict[str, Any]],
        auth_token: str,
        test_user_id: str,
        test_trace_id: str,
    ) -> None:
        """
        Flujo completo con categoría holistic (integral).
        Debe integrar recomendaciones de múltiples dimensiones.
        """
        request_payload = {
            "user_id": test_user_id,
            "category": "holistic",
            "metadata": {
                "context": "Quiero un plan integral para mejorar mi bienestar general.",
                "goals": ["reducir estrés", "aumentar energía", "conectar con propósito"],
            },
        }
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/holistic/advice",
            json=request_payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        
        result = data["result"]
        recommendations = result["recommendations"]
        
        # Validar que hay recomendaciones
        assert len(recommendations) > 0
        
        # Para holistic, puede haber recomendaciones de múltiples dimensiones
        dimensions = {rec["dimension"] for rec in recommendations}
        assert "integral" in dimensions  # Debe haber al menos recomendaciones integrales

    def test_vector_search_returns_relevant_results(
        self,
        verify_all_services: None,
        ingest_test_documents: list[dict[str, Any]],
        test_trace_id: str,
    ) -> None:
        """
        Valida que la búsqueda vectorial retorna resultados relevantes
        para los documentos ingestados.
        """
        # Buscar sobre meditación (debe encontrar el documento mind)
        search_payload = {
            "query": "técnicas de meditación para reducir estrés",
            "limit": 5,
            "filter": {
                "must": {
                    "trace_id": test_trace_id,
                }
            },
        }
        
        response = requests.post(
            f"{VECTORIAL_SERVICE_URL}/search",
            json=search_payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "hits" in data
        hits = data["hits"]
        assert len(hits) > 0
        
        # El hit más relevante debería ser sobre meditación
        top_hit = hits[0]
        assert "payload" in top_hit
        assert top_hit["payload"]["category"] == "mind"
        assert "meditación" in top_hit["payload"]["text"].lower()


class TestE2EErrorScenarios:
    """Pruebas E2E de escenarios de error."""

    def test_invalid_category_returns_error(
        self,
        verify_all_services: None,
        auth_token: str,
        test_user_id: str,
    ) -> None:
        """Valida que categorías inválidas retornan error apropiado."""
        request_payload = {
            "user_id": test_user_id,
            "category": "invalid_category",
            "metadata": {},
        }
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BACKEND_URL}/api/v1/holistic/advice",
            json=request_payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        
        # Debería retornar error
        assert response.status_code >= 400

    def test_unauthorized_request_returns_401(
        self,
        verify_all_services: None,
        test_user_id: str,
    ) -> None:
        """Valida que solicitudes sin autenticación retornan 401."""
        request_payload = {
            "user_id": test_user_id,
            "category": "mind",
            "metadata": {},
        }
        
        # Sin headers de autorización
        response = requests.post(
            f"{BACKEND_URL}/api/v1/holistic/advice",
            json=request_payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 401


class TestE2EPerformance:
    """Pruebas E2E de performance."""

    def test_concurrent_requests_are_handled(
        self,
        verify_all_services: None,
        ingest_test_documents: list[dict[str, Any]],
        auth_token: str,
        test_user_id: str,
    ) -> None:
        """
        Valida que el sistema puede manejar múltiples solicitudes concurrentes.
        """
        import concurrent.futures
        
        def make_request(category: str) -> dict[str, Any]:
            """Hace una solicitud al backend."""
            payload = {
                "user_id": test_user_id,
                "category": category,
                "metadata": {"test": "concurrent"},
            }
            headers = {"Authorization": f"Bearer {auth_token}"}
            
            response = requests.post(
                f"{BACKEND_URL}/api/v1/holistic/advice",
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            return response.json()
        
        # Hacer 3 solicitudes concurrentes
        categories = ["mind", "body", "soul"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, cat) for cat in categories]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Todas las solicitudes deben completarse exitosamente
        assert len(results) == 3
        for result in results:
            assert result["status"] == "completed"


# Funciones auxiliares

def _wait_for_job_completion(
    job_id: str,
    service_url: str,
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

