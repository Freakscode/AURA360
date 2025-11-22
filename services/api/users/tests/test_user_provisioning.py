"""Pruebas para la provisión de usuarios vía Supabase Admin API."""

import io
import json
import uuid
from unittest import mock

from django.db import connection
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from urllib.error import HTTPError

from users.authentication import SupabaseUser
from users.models import AppUser


class UserProvisioningTests(APITestCase):
    """Valida el endpoint /dashboard/users/provision/."""

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

    def _service_user(self) -> SupabaseUser:
        return SupabaseUser(id='service-role', email='service@example.com', role='service_role')

    @override_settings(
        SUPABASE_SERVICE_ROLE_KEY='service-key',
        SUPABASE_API_URL='http://localhost:54321',
        SUPABASE_ADMIN_TIMEOUT=1,
    )
    @mock.patch('users.services.supabase_admin.urlopen')
    def test_provision_creates_app_user(self, mock_urlopen):
        supabase_id = str(uuid.uuid4())
        response_payload = {
            'id': supabase_id,
            'email': 'paciente@aurademo.com',
        }

        mock_response = mock.MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = json.dumps(response_payload).encode('utf-8')
        mock_urlopen.return_value = mock_response

        self.client.force_authenticate(self._service_user())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer service-role-token')

        url = reverse('users:appuser-provision')
        request_payload = {
            'email': 'paciente@aurademo.com',
            'password': 'Aura360!',
            'email_confirm': True,
            'user_metadata': {
                'full_name': 'Paciente Demo',
                'role_global': 'Paciente',
                'billing_plan': 'individual',
                'tier': 'free',
                'is_independent': False,
                'age': 29,
                'gender': 'F',
            },
        }

        response = self.client.post(url, request_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AppUser.objects.filter(auth_user_id=supabase_id).exists())

        app_user = AppUser.objects.get(auth_user_id=supabase_id)
        self.assertEqual(app_user.full_name, 'Paciente Demo')
        self.assertEqual(app_user.tier, 'free')
        self.assertEqual(app_user.role_global, 'Paciente')
        self.assertFalse(app_user.is_independent)

        request_sent = mock_urlopen.call_args[0][0]
        sent_body = json.loads(request_sent.data.decode('utf-8'))
        self.assertTrue(sent_body['email_confirm'])
        self.assertEqual(sent_body['user_metadata']['tier'], 'free')

    @override_settings(
        SUPABASE_SERVICE_ROLE_KEY='service-key',
        SUPABASE_API_URL='http://localhost:54321',
        SUPABASE_ADMIN_TIMEOUT=1,
    )
    @mock.patch('users.services.supabase_admin.urlopen')
    def test_provision_return_validation_error(self, mock_urlopen):
        error_body = json.dumps({'message': 'Email already registered'}).encode('utf-8')
        mock_error = HTTPError(
            url='http://localhost:54321/auth/v1/admin/users',
            code=400,
            msg='Bad Request',
            hdrs=None,
            fp=io.BytesIO(error_body),
        )
        mock_urlopen.side_effect = mock_error

        self.client.force_authenticate(self._service_user())
        self.client.credentials(HTTP_AUTHORIZATION='Bearer service-role-token')

        url = reverse('users:appuser-provision')
        payload = {
            'email': 'paciente@aurademo.com',
            'password': 'Aura360!',
            'user_metadata': {
                'full_name': 'Paciente Demo',
                'role_global': 'Paciente',
                'billing_plan': 'individual',
                'tier': 'free',
                'is_independent': False,
                'age': 29,
            },
        }

        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Email already registered')
