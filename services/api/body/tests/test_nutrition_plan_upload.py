"""Pruebas para la carga de planes nutricionales en PDF."""

from __future__ import annotations

import io
import uuid
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from users.authentication import SupabaseUser
from body.services import (
    NutritionPlanIngestionError,
    NutritionPlanStorageError,
    NutritionPlanStorageResult,
)


class NutritionPlanUploadTests(TestCase):
    """Valida la capa de presentación del flujo de ingestión de planes."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.auth_user_id = uuid.uuid4()
        self.user = SupabaseUser(id=str(self.auth_user_id))
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test-token')

    def _build_pdf(self, *, size_bytes: int = 1024) -> SimpleUploadedFile:
        buffer = io.BytesIO(b"%PDF-1.4\n" + b"0" * (size_bytes - 9))
        return SimpleUploadedFile('plan.pdf', buffer.getvalue(), content_type='application/pdf')

    @mock.patch('body.views.enqueue_nutrition_plan_ingestion')
    @mock.patch('body.views.store_nutrition_plan_pdf')
    def test_upload_dispatches_job(self, mock_store, mock_enqueue):
        mock_store.return_value = NutritionPlanStorageResult(
            storage_kind='supabase',
            path='nutrition-plans/user/plan.pdf',
            bucket='plans',
            public_url='https://cdn.example.com/plan.pdf',
        )
        mock_enqueue.return_value = {'payload': {'status': 'accepted'}, 'request': {'job_id': '123'}}

        response = self.client.post(
            reverse('dashboard-nutrition-plan-upload'),
            {'plan_pdf': self._build_pdf(), 'title': 'Plan Octubre'},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.data)
        mock_store.assert_called_once()
        mock_enqueue.assert_called_once()
        payload = response.json()
        self.assertIn('job_id', payload)
        self.assertEqual(payload['ingest_response'], {'status': 'accepted'})

    def test_upload_requires_file(self):
        response = self.client.post(reverse('dashboard-nutrition-plan-upload'), {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'missing_file')

    def test_upload_rejects_non_pdf(self):
        file = SimpleUploadedFile('plan.txt', b'Hello', content_type='text/plain')
        response = self.client.post(
            reverse('dashboard-nutrition-plan-upload'),
            {'plan_pdf': file},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'invalid_content_type')

    @override_settings(NUTRITION_PLAN_MAX_UPLOAD_MB=0)
    def test_upload_rejects_large_files(self):
        response = self.client.post(
            reverse('dashboard-nutrition-plan-upload'),
            {'plan_pdf': self._build_pdf()},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'file_too_large')

    @mock.patch('body.views.store_nutrition_plan_pdf', side_effect=NutritionPlanStorageError('boom'))
    def test_storage_errors_are_reported(self, mock_store):
        response = self.client.post(
            reverse('dashboard-nutrition-plan-upload'),
            {'plan_pdf': self._build_pdf()},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.json()['error'], 'storage_error')

    @mock.patch('body.views.enqueue_nutrition_plan_ingestion', side_effect=NutritionPlanIngestionError('fail'))
    @mock.patch('body.views.store_nutrition_plan_pdf')
    def test_ingestion_errors_are_reported(self, mock_store, mock_enqueue):
        mock_store.return_value = NutritionPlanStorageResult(
            storage_kind='local',
            path='nutrition-plans/user/plan.pdf',
            bucket=None,
            public_url=None,
        )

        response = self.client.post(
            reverse('dashboard-nutrition-plan-upload'),
            {'plan_pdf': self._build_pdf()},
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(response.json()['error'], 'ingestion_error')


