"""Pruebas de integración para los endpoints de cuotas."""

import uuid

from django.contrib.auth import get_user_model
from django.db import connection
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import AppUser, UsageLedger


class QuotaEndpointTests(APITestCase):
    """Valida que los endpoints de cuota apliquen y consulten límites."""

    @classmethod
    def setUpTestData(cls):
        cls._ensure_app_users_table()

    @staticmethod
    def _ensure_app_users_table():
        """Crea la tabla app_users si no existe (necesaria para tests).
        
        Esta tabla existe en Supabase pero pytest crea una DB temporal,
        por lo que debemos recrearla manualmente para los tests.
        """
        vendor = connection.vendor
        with connection.cursor() as cursor:
            if vendor == 'sqlite':
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        auth_user_id TEXT UNIQUE,
                        full_name TEXT NOT NULL,
                        age INTEGER NOT NULL DEFAULT 0,
                        email TEXT UNIQUE,
                        phone_number TEXT,
                        gender TEXT,
                        tier TEXT NOT NULL,
                        role_global TEXT NOT NULL DEFAULT 'General',
                        is_independent BOOLEAN NOT NULL DEFAULT 0,
                        billing_plan TEXT NOT NULL DEFAULT 'individual',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            else:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_users (
                        id BIGSERIAL PRIMARY KEY,
                        auth_user_id UUID UNIQUE,
                        full_name TEXT NOT NULL,
                        age INTEGER NOT NULL DEFAULT 0,
                        email TEXT UNIQUE,
                        phone_number TEXT,
                        gender TEXT,
                        tier TEXT NOT NULL,
                        role_global TEXT NOT NULL DEFAULT 'General',
                        is_independent BOOLEAN NOT NULL DEFAULT FALSE,
                        billing_plan TEXT NOT NULL DEFAULT 'individual',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                    """
                )

    def setUp(self):
        user_model = get_user_model()
        self.auth_user = user_model.objects.create_user('tester', 'tester@example.com', 'secret')
        self.client.force_authenticate(self.auth_user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer integration-test-token')

    def _create_app_user(self, tier: str, email: str = None) -> AppUser:
        email = email or f'{tier}-{uuid.uuid4()}@example.com'
        return AppUser.objects.create(
            auth_user_id=uuid.uuid4(),
            full_name=f'User {tier}',
            age=30,
            email=email,
            tier=tier,
        )

    def test_generate_metabolic_report_respects_monthly_limit(self):
        app_user = self._create_app_user('free')
        url = reverse('users:appuser-generate-metabolic-report', args=[app_user.id])

        first = self.client.post(url)
        self.assertEqual(first.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(first.data['quota']['remaining'], 0)

        second = self.client.post(url)
        self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(second.data['detail'], 'quota_exceeded')

    def test_realtime_update_unlimited_for_core(self):
        app_user = self._create_app_user('core')
        url = reverse('users:appuser-request-realtime-update', args=[app_user.id])

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIsNone(response.data['limit'])
        self.assertIsNone(response.data['remaining'])

    def test_chatbot_session_respects_daily_limit(self):
        app_user = self._create_app_user('plus')
        url = reverse('users:appuser-chatbot-session', args=[app_user.id])

        for _ in range(20):
            resp = self.client.post(url)
            self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)

        blocked = self.client.post(url)
        self.assertEqual(blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_quota_status_endpoint_returns_snapshot(self):
        app_user = self._create_app_user('free')
        consume_url = reverse('users:appuser-generate-metabolic-report', args=[app_user.id])
        self.client.post(consume_url)

        status_url = reverse('users:appuser-quota-status', args=[app_user.id])
        response = self.client.get(status_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(item['resource_code'] == 'metabolic_report' for item in response.data))

    def test_usage_history_lists_events(self):
        app_user = self._create_app_user('core')
        url = reverse('users:appuser-request-realtime-update', args=[app_user.id])
        self.client.post(url)

        history_url = reverse('users:appuser-usage-history', args=[app_user.id])
        response = self.client.get(history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['resource_code'], 'realtime_update')

    def test_usage_history_limit_parameter(self):
        app_user = self._create_app_user('core')
        url = reverse('users:appuser-request-realtime-update', args=[app_user.id])
        for _ in range(5):
            self.client.post(url)

        history_url = reverse('users:appuser-usage-history', args=[app_user.id]) + '?limit=2'
        response = self.client.get(history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # Asegura orden descendente
        timestamps = [entry['occurred_at'] for entry in response.data]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def tearDown(self):
        UsageLedger.objects.all().delete()
