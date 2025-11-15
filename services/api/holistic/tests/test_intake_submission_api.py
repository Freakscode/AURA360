from __future__ import annotations

import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from holistic.models import IntakeSubmission


class _StubUser:
    def __init__(self, user_id: uuid.UUID):
        self.id = user_id

    @property
    def is_authenticated(self) -> bool:  # pragma: no cover - DRF check
        return True


class IntakeSubmissionAPITests(APITestCase):
    endpoint_name = "holistic:intake-submissions"

    def setUp(self):
        super().setUp()
        self.user_id = uuid.uuid4()
        self.stub_user = _StubUser(self.user_id)
        self.client.force_authenticate(user=self.stub_user)
        self.list_url = reverse(self.endpoint_name)

    # Helpers -----------------------------------------------------------------
    def _build_valid_answers(self) -> list[dict[str, object]]:
        return [
            {"question_id": "F1", "value": "moderate"},
            {"question_id": "F2", "value": "weekly_3_4"},
            {
                "question_id": "F3",
                "value": {
                    "frequency": "three_four",
                    "consulted_professional": False,
                },
            },
            {
                "question_id": "F4",
                "value": {"selected": ["sedentarism", "screen_overuse"]},
            },
            {"question_id": "M1", "value": "high"},
            {
                "question_id": "M2",
                "value": {"selected": ["work", "relationships"]},
            },
            {"question_id": "M3", "value": "weekly_1_2"},
            {
                "question_id": "M4",
                "value": {
                    "has_strategies": True,
                    "strategies": {"selected": ["breathing", "therapy"]},
                },
            },
            {"question_id": "S1", "value": "partially_aligned"},
            {
                "question_id": "S2",
                "value": {"selected": ["meditation", "gratitude"]},
            },
            {"question_id": "S3", "value": "high"},
            {
                "question_id": "S4",
                "value": {"has_guide": True, "guide_type": "community"},
            },
        ]

    # Tests -------------------------------------------------------------------
    def test_create_submission_returns_201(self):
        payload = {
            "answers": self._build_valid_answers(),
            "free_text": "Busco reducir estrés y ordenar mi rutina",
            "vectorize_snapshot": True,
        }

        response = self.client.post(self.list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertIn("id", body)
        self.assertEqual(body["status"], "pending")
        self.assertEqual(body["free_text"], payload["free_text"])
        submission = IntakeSubmission.objects.get(id=body["id"])
        self.assertEqual(submission.auth_user_id, self.user_id)
        self.assertIn("F1", submission.answers)

    def test_missing_question_returns_error(self):
        answers = self._build_valid_answers()[:-1]  # remove last question
        response = self.client.post(
            self.list_url,
            {"answers": answers},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Faltan respuestas", response.json()["answers"][0])

    def test_list_returns_user_submissions(self):
        IntakeSubmission.objects.create(
            auth_user_id=self.user_id,
            answers={"F1": "moderate"},
            free_text="",
        )
        IntakeSubmission.objects.create(
            auth_user_id=self.user_id,
            answers={"F1": "good"},
            free_text="",
        )

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(body["count"], 2)
        self.assertEqual(len(body["results"]), 2)

    def test_detail_scope_isolated_per_user(self):
        submission = IntakeSubmission.objects.create(
            auth_user_id=self.user_id,
            answers={"F1": "moderate"},
            free_text="",
        )
        other_submission = IntakeSubmission.objects.create(
            auth_user_id=uuid.uuid4(),
            answers={"F1": "good"},
            free_text="",
        )

        detail_url = reverse("holistic:intake-submission-detail", args=[submission.id])
        response_ok = self.client.get(detail_url)
        self.assertEqual(response_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(response_ok.json()["id"], str(submission.id))

        detail_url_forbidden = reverse("holistic:intake-submission-detail", args=[other_submission.id])
        response_not_found = self.client.get(detail_url_forbidden)
        self.assertEqual(response_not_found.status_code, status.HTTP_404_NOT_FOUND)
