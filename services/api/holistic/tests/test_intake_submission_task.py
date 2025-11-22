from __future__ import annotations

import uuid
from unittest import mock

from django.test import TestCase

from holistic.models import HolisticAgentProfile, HolisticCategory, IntakeSubmission
from holistic.tasks import process_intake_submission


class ProcessIntakeSubmissionTaskTests(TestCase):
    def setUp(self):
        self.user_id = uuid.uuid4()
        self.submission = IntakeSubmission.objects.create(
            auth_user_id=self.user_id,
            answers={"F1": "moderate"},
            free_text="Necesito balancear mi energía",
        )

    @mock.patch("holistic.reporting.generate_personalized_report", return_value={"url": "https://cdn.example.com/report.pdf"})
    @mock.patch("holistic.services.persist_vector_queries")
    @mock.patch("holistic.services.create_agent_run")
    @mock.patch("holistic.services.call_agent_service")
    @mock.patch("holistic.services.fetch_user_profile", return_value={"id": "user"})
    @mock.patch("holistic.context_vectorizer.UserContextVectorizer")
    @mock.patch("holistic.context_aggregator.UserContextAggregator")
    def test_process_intake_submission_success(
        self,
        aggregator_mock,
        vectorizer_mock,
        fetch_profile_mock,
        call_agent_service_mock,
        create_agent_run_mock,
        persist_vector_queries_mock,
        generate_report_mock,
    ):
        aggregator_instance = aggregator_mock.return_value
        aggregator_instance.aggregate_holistic_context.return_value = {
            "text": "Contexto consolidado",
            "metadata": {"score": 0.8},
        }

        call_agent_service_mock.return_value = {
            "status": "success",
            "data": {"summary": {"title": "Mock"}, "vector_queries": []},
            "latency_ms": 123,
        }

        HolisticAgentProfile.objects.create(
            category=HolisticCategory.HOLISTIC,
            primary_agent="agent-holistic",
            fallback_agents=["agent-fallback"],
            embedding_model="fast-embed-384",
            prompt_template="Prompt",
            version="1.0.0",
            is_active=True,
        )

        result = process_intake_submission(str(self.submission.id))

        self.assertEqual(result["status"], "completed")
        refreshed = IntakeSubmission.objects.get(id=self.submission.id)
        self.assertEqual(refreshed.status, "ready")
        self.assertEqual(refreshed.processing_stage, "report_ready")
        self.assertTrue(generate_report_mock.called)
        self.assertTrue(create_agent_run_mock.called)

    @mock.patch("holistic.context_vectorizer.UserContextVectorizer")
    @mock.patch("holistic.context_aggregator.UserContextAggregator")
    def test_process_intake_submission_without_profile_marks_failed(
        self,
        aggregator_mock,
        vectorizer_mock,
    ):
        aggregator_mock.return_value.aggregate_holistic_context.return_value = {
            "text": "Context",
            "metadata": {},
        }

        result = process_intake_submission(str(self.submission.id))

        self.assertEqual(result["status"], "failed")
        refreshed = IntakeSubmission.objects.get(id=self.submission.id)
        self.assertEqual(refreshed.status, "failed")
