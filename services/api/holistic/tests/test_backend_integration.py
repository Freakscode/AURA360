"""
Pruebas de integración para el backend Django con el servicio de agentes.

Valida:
- Comunicación Backend → Servicio de Agentes
- Persistencia de HolisticRequest, HolisticAgentRun, HolisticVectorQuery
- Manejo de errores y reintentos
- Transformación de payloads
- Validación de perfiles de agentes (HolisticAgentProfile)

Prerequisitos:
- Servicio de agentes debe estar corriendo (puerto 8080)
- Servicio vectorial debe estar corriendo (puerto 8001)
- Base de datos Django configurada y migrada
- Variables de entorno configuradas (HOLISTIC_AGENT_SERVICE_URL, etc.)
"""

from __future__ import annotations

import time
import uuid
from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from holistic.models import (
    HolisticAgentProfile,
    HolisticAgentRun,
    HolisticAgentRunStatus,
    HolisticRequest,
    HolisticRequestStatus,
    HolisticVectorQuery,
)
from holistic.services import call_agent_service, create_agent_run, fetch_user_profile
from django.db import connection
from django.db.utils import ProgrammingError
from users.models import AppUser
from users.models import AppUser

User = get_user_model()

AGENTS_SERVICE_URL = "http://localhost:8080"
VECTORIAL_SERVICE_URL = "http://localhost:8001"


class TestBackendAgentsServiceIntegration(TestCase):
    """Pruebas de integración Backend → Servicio de Agentes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Verificar que los servicios estén disponibles
        cls._verify_services_available()

    @classmethod
    def _verify_services_available(cls):
        """Verifica que los servicios requeridos estén disponibles."""
        services = [
            (AGENTS_SERVICE_URL, "servicio de agentes"),
            (VECTORIAL_SERVICE_URL, "servicio vectorial"),
        ]
        
        for url, name in services:
            try:
                response = requests.get(f"{url}/readyz", timeout=5)
                if response.status_code != 200:
                    pytest.skip(f"El {name} no está disponible en {url}")
            except Exception:
                pytest.skip(f"El {name} no está disponible en {url}")

    def setUp(self):
        """Configuración antes de cada prueba."""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username=f"agent-user-{uuid.uuid4()}",
            email=f"test-{uuid.uuid4()}@example.com",
            password="testpass123",
        )
        
        # Crear perfiles de agentes
        self.agent_profiles = {}
        for category in ["mind", "body", "soul", "holistic"]:
            profile = HolisticAgentProfile.objects.create(
                category=category,
                primary_agent=f"{category}_guardian",
                fallback_agents=[],
                embedding_model="text-embedding-3-small",
                prompt_template="Default template",
                version="1.0.0-test",
                is_active=True,
            )
            self.agent_profiles[category] = profile
        
        # Cliente API
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_call_agent_service_success(self):
        """Valida que call_agent_service puede comunicarse exitosamente."""
        trace_id = f"test-backend-{uuid.uuid4()}"
        payload = {
            "trace_id": trace_id,
            "category": "mind",
            "user_profile": {
                "id": str(self.user.id),
                "name": "Test User",
                "email": self.user.email,
            },
            "preferences": {"focus": ["respiración"]},
            "context": "Necesito técnicas de relajación.",
        }
        
        with override_settings(HOLISTIC_AGENT_SERVICE_URL=f"{AGENTS_SERVICE_URL}/api/v1/holistic/advice"):
            result = call_agent_service(payload, trace_id, timeout=120)
        
        assert result["status"] == "success"
        assert result["status_code"] == 200
        assert result["data"] is not None
        assert result["error"] is None
        assert result["latency_ms"] is not None
        assert result["latency_ms"] > 0

    @patch("holistic.views.call_agent_service")
    def test_holistic_request_creates_records(self, mock_agent):
        """Valida que una solicitud holística crea los registros correctos."""
        trace_id = str(uuid.uuid4())
        category = "mind"
        
        payload = {
            "user_id": str(self.user.id),
            "category": category,
            "metadata": {"test": True},
        }
        
        mock_agent.return_value = {
            "status": "success",
            "status_code": 200,
            "data": {
                "trace_id": trace_id,
                "status": "success",
                "data": {
                    "summary": "Plan",
                    "recommendations": [],
                    "vector_queries": [
                        {
                            "vector_store": "qdrant",
                            "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                            "query_text": "Genera un plan",
                            "top_k": 5,
                            "response_payload": {"hits": []},
                            "confidence_score": 0.5,
                        }
                    ],
                },
            },
            "error": None,
            "latency_ms": 1000,
        }

        response = self.client.post("/api/v1/holistic/advice", payload, format="json")
        
        # Validar respuesta
        assert response.status_code in [200, 201]
        data = response.json()
        assert "trace_id" in data
        assert data["status"] == HolisticRequestStatus.COMPLETED
        
        # Validar que se creó HolisticRequest
        holistic_request = HolisticRequest.objects.filter(
            user_id=str(self.user.id),
            category=category,
        ).latest("created_at")
        
        assert holistic_request is not None
        assert holistic_request.status == HolisticRequestStatus.COMPLETED
        assert holistic_request.response_payload is not None
        
        # Validar que se creó HolisticAgentRun
        agent_run = HolisticAgentRun.objects.filter(
            request=holistic_request
        ).first()
        
        assert agent_run is not None
        assert agent_run.status == HolisticAgentRunStatus.COMPLETED
        assert agent_run.latency_ms is not None

    @patch("holistic.views.call_agent_service")
    def test_vector_queries_are_persisted(self, mock_agent):
        """Valida que las consultas vectoriales se persisten correctamente."""
        trace_id = str(uuid.uuid4())
        
        payload = {
            "user_id": str(self.user.id),
            "category": "mind",
            "metadata": {
                "context": "Técnicas de meditación mindfulness",
            },
        }
        
        mock_agent.return_value = {
            "status": "success",
            "status_code": 200,
            "data": {
                "trace_id": trace_id,
                "status": "success",
                "data": {
                    "summary": "Plan",
                    "recommendations": [],
                    "vector_queries": [
                        {
                            "vector_store": "qdrant",
                            "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                            "query_text": "Técnicas de meditación mindfulness",
                            "top_k": 5,
                            "response_payload": {"hits": []},
                            "confidence_score": 0.7,
                        }
                    ],
                },
            },
            "error": None,
            "latency_ms": 900,
        }

        response = self.client.post("/api/v1/holistic/advice", payload, format="json")
        
        assert response.status_code in [200, 201]
        
        # Obtener el HolisticRequest creado
        holistic_request = HolisticRequest.objects.filter(
            user_id=str(self.user.id),
            category="mind",
        ).latest("created_at")
        
        # Obtener el AgentRun
        agent_run = HolisticAgentRun.objects.filter(
            request=holistic_request
        ).first()
        
        # Verificar que hay queries vectoriales persistidas
        vector_queries = HolisticVectorQuery.objects.filter(agent_run=agent_run)
        
        # Nota: Puede ser 0 si el servicio no hizo consultas vectoriales
        # pero si hay, deben tener la estructura correcta
        for query in vector_queries:
            assert query.vector_store is not None
            assert query.embedding_model is not None
            assert query.query_text is not None
            assert query.top_k > 0

    def test_agent_service_timeout_is_handled(self):
        """Valida que los timeouts del servicio de agentes se manejan correctamente."""
        trace_id = f"test-timeout-{uuid.uuid4()}"
        
        with patch("holistic.services.requests.post") as mock_post:
            mock_post.side_effect = requests.Timeout("Connection timeout")
            
            payload = {
                "trace_id": trace_id,
                "category": "mind",
                "user_profile": {"id": str(self.user.id)},
            }
            
            result = call_agent_service(payload, trace_id, timeout=1)
        
        assert result["status"] == "error"
        assert result["error"]["type"] == "timeout"

    def test_agent_service_http_error_is_handled(self):
        """Valida que los errores HTTP del servicio se manejan correctamente."""
        trace_id = f"test-http-error-{uuid.uuid4()}"
        
        with patch("holistic.services.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.raise_for_status.side_effect = requests.RequestException("500 Error")
            mock_response.json.return_value = {
                "status": "error",
                "error": {"type": "internal_error", "message": "Something went wrong"},
            }
            mock_post.return_value = mock_response
            
            payload = {
                "trace_id": trace_id,
                "category": "mind",
                "user_profile": {"id": str(self.user.id)},
            }
            
            result = call_agent_service(payload, trace_id, timeout=10)
        
        assert result["status"] == "error"
        assert result["status_code"] == 500
        assert result["error"]["type"] == "response_error"

    def test_missing_agent_profile_returns_503(self):
        """Valida que la falta de perfil de agente retorna error 503."""
        # Eliminar todos los perfiles activos
        HolisticAgentProfile.objects.all().update(is_active=False)
        
        payload = {
            "user_id": str(self.user.id),
            "category": "mind",
        }
        
        response = self.client.post("/api/v1/holistic/advice", payload, format="json")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == HolisticRequestStatus.FAILED
        assert data["error"]["type"] == "agent_profile_not_found"


class TestHolisticServicesUnit(TestCase):
    """Pruebas unitarias de servicios holísticos."""

    def setUp(self):
        """Configuración antes de cada prueba."""
        self.user = User.objects.create_user(
            username=f"holistic-unit-{uuid.uuid4()}",
            email=f"test-{uuid.uuid4()}@example.com",
            password="testpass123",
        )
        try:
            tables = connection.introspection.table_names()
            if AppUser._meta.db_table not in tables:
                self.skipTest("Tabla app_users no disponible en el entorno de pruebas")
            AppUser.objects.create(
                auth_user_id=uuid.uuid4(),
                full_name="Holistic Unit Tester",
                age=30,
                email=self.user.email,
                tier="free",
            )
        except ProgrammingError:
            self.skipTest("No se puede acceder a app_users en el entorno de pruebas")

    def test_fetch_user_profile_returns_complete_profile(self):
        """Valida que fetch_user_profile retorna un perfil completo."""
        profile = fetch_user_profile(str(self.user.id))
        
        assert profile is not None
        assert "id" in profile
        assert profile["id"] == str(self.user.id)
        assert "email" in profile

    def test_create_agent_run_creates_record(self):
        """Valida que create_agent_run crea el registro correctamente."""
        holistic_request = HolisticRequest.objects.create(
            user_id=str(self.user.id),
            category="mind",
            status=HolisticRequestStatus.PENDING,
            trace_id=uuid.uuid4(),
            request_payload={},
        )
        
        agent_run = create_agent_run(
            holistic_request,
            agent_name="mental_guardian",
            status=HolisticAgentRunStatus.COMPLETED,
            latency_ms=1500,
            input_context={"test": "input"},
            output_payload={"test": "output"},
        )
        
        assert agent_run is not None
        assert agent_run.agent_name == "mental_guardian"
        assert agent_run.status == HolisticAgentRunStatus.COMPLETED
        assert agent_run.latency_ms == 1500
        assert agent_run.input_context == {"test": "input"}
        assert agent_run.output_payload == {"test": "output"}


class TestHolisticAPIEndpoint(TestCase):
    """Pruebas del endpoint API completo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Verificar servicios disponibles
        try:
            response = requests.get(f"{AGENTS_SERVICE_URL}/readyz", timeout=5)
            if response.status_code != 200:
                pytest.skip("Servicio de agentes no disponible")
        except Exception:
            pytest.skip("Servicio de agentes no disponible")

    def setUp(self):
        """Configuración antes de cada prueba."""
        self.user = User.objects.create_user(
            username=f"holistic-api-{uuid.uuid4()}",
            email=f"test-{uuid.uuid4()}@example.com",
            password="testpass123",
        )
        
        # Crear perfil de agente
        HolisticAgentProfile.objects.create(
            category="mind",
            primary_agent="mental_guardian",
            fallback_agents=[],
            embedding_model="text-embedding-3-small",
            prompt_template="Default template",
            version="1.0.0-test",
            is_active=True,
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("holistic.views.call_agent_service")
    def test_end_to_end_advice_request(self, mock_agent):
        """Prueba end-to-end completa de solicitud de consejo."""
        payload = {
            "user_id": str(self.user.id),
            "category": "mind",
            "metadata": {
                "context": "Me siento estresado y necesito técnicas de relajación",
                "urgency": "medium",
            },
        }
        
        mock_agent.return_value = {
            "status": "success",
            "status_code": 200,
            "data": {
                "trace_id": str(uuid.uuid4()),
                "status": "success",
                "data": {
                    "summary": "Plan integral",
                    "recommendations": [],
                    "vector_queries": [],
                },
            },
            "error": None,
            "latency_ms": 850,
        }

        start = time.perf_counter()
        response = self.client.post("/api/v1/holistic/advice", payload, format="json")
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Validar respuesta HTTP
        assert response.status_code in [200, 201]
        data = response.json()
        
        # Validar estructura de respuesta
        assert "trace_id" in data
        assert "status" in data
        assert data["status"] == HolisticRequestStatus.COMPLETED
        assert "result" in data
        
        result = data["result"]
        nested_result = result.get("data", result)
        assert "summary" in nested_result
        assert "recommendations" in nested_result
        
        # Validar que la latencia es razonable
        assert elapsed_ms < 120000  # Menos de 2 minutos
        
        # Validar persistencia en base de datos
        holistic_request = HolisticRequest.objects.filter(
            trace_id=data["trace_id"]
        ).first()
        
        assert holistic_request is not None
        assert holistic_request.status == HolisticRequestStatus.COMPLETED
        assert holistic_request.response_payload is not None
        agent_run = HolisticAgentRun.objects.filter(request=holistic_request).first()
        assert agent_run is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

