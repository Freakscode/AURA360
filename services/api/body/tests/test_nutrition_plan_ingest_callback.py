from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


def _base_plan_data() -> dict:
    return {
        "plan": {
            "title": "Plan nutricional",
            "language": "es",
            "source": {"kind": "pdf", "uri": "https://cdn.example.com/plan.pdf"},
        },
        "subject": {"user_id": "user-1"},
        "assessment": {},
        "directives": {"meals": []},
        "supplements": [],
        "recommendations": [],
    }


def _payload(**overrides) -> dict:
    base = {
        "job_id": str(uuid.uuid4()),
        "auth_user_id": str(uuid.uuid4()),
        "title": "Plan nutricional",
        "language": "es",
        "is_active": True,
        "plan_data": _base_plan_data(),
        "source": {
            "kind": "pdf",
            "storage_kind": "supabase",
            "path": "nutrition-plans/user/plan.pdf",
            "bucket": "nutrition-plans",
            "public_url": "https://cdn.example.com/plan.pdf",
        },
        "extractor": {
            "name": "deepseek-7b",
            "model": "deepseek-7b",
            "extracted_at": "2025-10-29T10:00:00Z",
        },
        "metadata": {},
    }
    base.update(overrides)
    return base


@override_settings(NUTRITION_PLAN_CALLBACK_TOKEN="callback-secret")
class NutritionPlanIngestCallbackTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = reverse("nutrition-plan-ingest-callback")

    @mock.patch("body.views.NutritionPlanSerializer")
    def test_callback_creates_new_plan(self, serializer_cls):
        payload = _payload()
        serializer_instance = serializer_cls.return_value
        serializer_instance.is_valid.return_value = True
        persisted_plan = SimpleNamespace(
            id=uuid.uuid4(), title=payload["title"], auth_user_id=uuid.UUID(payload["auth_user_id"])
        )
        serializer_instance.save.return_value = persisted_plan

        response = self.client.post(
            self.url,
            payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer callback-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        plan_id = response.json()["plan_id"]
        self.assertEqual(plan_id, str(persisted_plan.id))
        self.assertEqual(response.json()["status"], "created")
        serializer_instance.is_valid.assert_called_once_with(raise_exception=True)
        serializer_instance.save.assert_called_once()

    def test_callback_requires_bearer_token(self):
        response = self.client.post(self.url, _payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch("body.views.NutritionPlan.objects.get")
    @mock.patch("body.views.NutritionPlanSerializer")
    def test_callback_updates_existing_plan(self, serializer_cls, get_plan):
        plan_id = uuid.uuid4()
        payload = _payload(metadata={"plan_id": str(plan_id)}, title="Plan actualizado")
        serializer_instance = serializer_cls.return_value
        serializer_instance.is_valid.return_value = True
        persisted_plan = SimpleNamespace(id=plan_id, title="Plan actualizado")
        serializer_instance.save.side_effect = [persisted_plan]
        get_plan.return_value = persisted_plan

        response = self.client.post(
            self.url,
            payload,
            format="json",
            HTTP_AUTHORIZATION="Bearer callback-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.json()["status"], "updated")
        get_plan.assert_called_once_with(id=str(plan_id))
        serializer_instance.is_valid.assert_called_once_with(raise_exception=True)

