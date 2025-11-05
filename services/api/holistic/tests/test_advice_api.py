from __future__ import annotations

import uuid

import responses
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from holistic.models import (
    HolisticAgentProfile,
    HolisticAgentRun,
    HolisticAgentRunStatus,
    HolisticRequest,
    HolisticRequestStatus,
    HolisticVectorQuery,
)


class HolisticAdviceAPITests(APITestCase):
    """Pruebas del endpoint /api/holistic/advice/."""

    endpoint_name = "holistic:holistic-advice"

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.auth_user = user_model.objects.create_user(
            username="holistic-tester",
            email="holistic-tester@example.com",
            password="holistic-pass",
        )

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(self.auth_user)
        self.override = override_settings(
            HOLISTIC_AGENT_SERVICE_URL="https://agent.example.com/run",
            HOLISTIC_AGENT_SERVICE_TOKEN="test-token",
            HOLISTIC_AGENT_REQUEST_TIMEOUT=5,
            HOLISTIC_AGENT_RETRY_DELAY=0,
        )
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.endpoint_url = reverse(self.endpoint_name)

    def tearDown(self):
        super().tearDown()
        HolisticAgentProfile.objects.all().delete()
        HolisticRequest.objects.all().delete()
        HolisticAgentRun.objects.all().delete()
        HolisticVectorQuery.objects.all().delete()

    def _create_profile(self, *, category: str = HolisticAgentProfile.category.field.choices[0][0]) -> HolisticAgentProfile:
        """Crea un perfil de agente activo para pruebas."""
        return HolisticAgentProfile.objects.create(
            category=category,
            primary_agent="agent-core-mind",
            fallback_agents=["agent-fallback-1"],
            embedding_model="fast-embed-384",
            prompt_template="Prompt base para pruebas.",
            version=f"1.0.{uuid.uuid4().hex[:6]}",
            is_active=True,
        )

    @responses.activate
    def test_valid_request_persists_entities(self):
        profile = self._create_profile(category="mind")
        agent_payload = {
            "result": {
                "summary": {"title": "Test", "message": "Contenido de prueba"},
                "recommendations": [],
            },
            "vector_queries": [
                {
                    "vector_store": "holistic_memory",
                    "embedding_model": "fast-embed-384",
                    "query_text": "latest habits",
                    "top_k": 3,
                    "response_payload": {"hits": []},
                    "confidence_score": 0.82,
                }
            ],
        }
        responses.add(
            responses.POST,
            "https://agent.example.com/run",
            json=agent_payload,
            status=200,
        )

        payload = {
            "user_id": str(uuid.uuid4()),
            "category": profile.category,
            "metadata": {"locale": "es-MX"},
        }
        response = self.client.post(self.endpoint_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["status"], HolisticRequestStatus.COMPLETED)
        self.assertIn("trace_id", body)
        self.assertEqual(body["result"], agent_payload)

        stored_request = HolisticRequest.objects.get(trace_id=body["trace_id"])
        self.assertEqual(stored_request.status, HolisticRequestStatus.COMPLETED)
        self.assertEqual(stored_request.response_payload, agent_payload)

        agent_run = HolisticAgentRun.objects.get(request=stored_request)
        self.assertEqual(agent_run.status, HolisticAgentRunStatus.COMPLETED)
        self.assertEqual(agent_run.agent_name, profile.primary_agent)

        vector_queries = HolisticVectorQuery.objects.filter(agent_run=agent_run)
        self.assertEqual(vector_queries.count(), 1)
        self.assertEqual(vector_queries.first().vector_store, "holistic_memory")

    def test_returns_503_when_agent_profile_missing(self):
        payload = {
            "user_id": str(uuid.uuid4()),
            "category": "mind",
        }
        response = self.client.post(self.endpoint_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        stored_request = HolisticRequest.objects.get()
        self.assertEqual(stored_request.status, HolisticRequestStatus.FAILED)
        self.assertEqual(stored_request.error_type, "agent_profile_not_found")

    @responses.activate
    def test_agent_service_failure_marks_request_failed(self):
        profile = self._create_profile(category="mind")
        responses.add(
            responses.POST,
            "https://agent.example.com/run",
            json={"detail": "upstream error"},
            status=500,
        )

        payload = {
            "user_id": str(uuid.uuid4()),
            "category": profile.category,
        }
        response = self.client.post(self.endpoint_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        stored_request = HolisticRequest.objects.get()
        self.assertEqual(stored_request.status, HolisticRequestStatus.FAILED)
        self.assertEqual(stored_request.error_type, "response_error")

        agent_run = HolisticAgentRun.objects.get(request=stored_request)
        self.assertEqual(agent_run.status, HolisticAgentRunStatus.FAILED)
        self.assertEqual(agent_run.error_type, "response_error")

    def test_invalid_category_validation_error(self):
        payload = {
            "user_id": str(uuid.uuid4()),
            "category": "invalid",
        }
        response = self.client.post(self.endpoint_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(HolisticRequest.objects.exists())