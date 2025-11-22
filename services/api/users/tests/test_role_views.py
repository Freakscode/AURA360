"""Pruebas básicas para la gestión de usuarios por roles."""

import uuid

from django.db import connection
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.authentication import SupabaseUser
from users.models import AppUser


class RoleViewsTests(APITestCase):
    """Valida los endpoints de gestión por rol."""

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
        AppUser.objects.all().delete()
        self.admin = AppUser.objects.create(
            auth_user_id=uuid.uuid4(),
            full_name='Admin Sistema',
            age=35,
            email='admin@aurademo.com',
            tier='premium',
            role_global='AdminSistema',
            billing_plan='corporate',
            is_independent=False,
        )
        self.paciente = AppUser.objects.create(
            auth_user_id=uuid.uuid4(),
            full_name='Paciente Demo',
            age=29,
            email='paciente@aurademo.com',
            tier='free',
            role_global='Paciente',
            billing_plan='individual',
            is_independent=True,
        )
        self.pro = AppUser.objects.create(
            auth_user_id=uuid.uuid4(),
            full_name='Profesional Demo',
            age=40,
            email='pro@aurademo.com',
            tier='premium',
            role_global='ProfesionalSalud',
            billing_plan='institution',
            is_independent=False,
        )

    def test_roles_summary(self):
        url = reverse('users:appuser-roles-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = {item['role_global']: item['total'] for item in response.data}
        self.assertEqual(payload.get('AdminSistema'), 1)
        self.assertEqual(payload.get('Paciente'), 1)
        self.assertEqual(payload.get('ProfesionalSalud'), 1)

    def test_role_members_listing(self):
        url = reverse('users:appuser-role-members', kwargs={'role_slug': 'paciente'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['email'], 'paciente@aurademo.com')

    def _service_user(self) -> SupabaseUser:
        return SupabaseUser(id='service-role', email='service@example.com', role='service_role')

    @override_settings(SUPABASE_SERVICE_ROLE_KEY='service-key')
    def test_set_role_updates_user(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer service-key')
        self.client.force_authenticate(self._service_user())

        url = reverse('users:appuser-set-role', args=[self.paciente.id])
        response = self.client.post(
            url,
            {
                'role_global': 'ProfesionalSalud',
                'is_independent': False,
                'billing_plan': 'institution',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.role_global, 'ProfesionalSalud')
        self.assertFalse(self.paciente.is_independent)
        self.assertEqual(self.paciente.billing_plan, 'institution')
