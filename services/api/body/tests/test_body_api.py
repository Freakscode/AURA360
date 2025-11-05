"""Pruebas para los endpoints del dominio Body."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from users.authentication import SupabaseUser


class BodyApiTests(TestCase):
    """Valida la interacción básica con el backend de hábitos corporales."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.auth_user_id = uuid.uuid4()
        self.user = SupabaseUser(id=str(self.auth_user_id))
        # Simula autenticación JWT
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer test-token')

    def test_create_entries_and_fetch_dashboard(self):
        """Crea registros a través de la API y valida el snapshot."""

        activity_payload = {
            'activity_type': 'cardio',
            'intensity': 'moderate',
            'duration_minutes': 45,
            'session_date': timezone.now().date().isoformat(),
            'notes': 'Sesión matutina.',
        }
        response = self.client.post(
            reverse('body-activities-list'),
            activity_payload,
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)

        nutrition_payload = {
            'meal_type': 'lunch',
            'timestamp': timezone.now().isoformat(),
            'items': ['Quinoa', 'Verduras'],
            'calories': 520,
            'protein': 32,
            'carbs': 48,
            'fats': 18,
            'notes': 'Comida balanceada.',
        }
        response = self.client.post(
            reverse('body-nutrition-list'),
            nutrition_payload,
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)

        bedtime = timezone.now().replace(hour=23, minute=0, second=0, microsecond=0)
        wake_time = bedtime + timedelta(hours=7)
        sleep_payload = {
            'bedtime': bedtime.isoformat(),
            'wake_time': wake_time.isoformat(),
            'duration_hours': 7.0,
            'quality': 'good',
            'notes': 'Descanso adecuado.',
        }
        response = self.client.post(
            reverse('body-sleep-list'),
            sleep_payload,
            format='json',
        )
        self.assertEqual(response.status_code, 201, response.data)

        snapshot_response = self.client.get(reverse('body-dashboard'))
        self.assertEqual(snapshot_response.status_code, 200, snapshot_response.data)

        snapshot = snapshot_response.json()
        self.assertEqual(len(snapshot['activities']), 1)
        self.assertEqual(len(snapshot['nutrition']), 1)
        self.assertEqual(len(snapshot['sleep']), 1)

    def test_entries_are_scoped_per_user(self):
        """Verifica que cada usuario sólo vea sus propios registros."""

        # Usuario original crea un registro de actividad
        self.client.post(
            reverse('body-activities-list'),
            {
                'activity_type': 'strength',
                'intensity': 'high',
                'duration_minutes': 30,
                'session_date': timezone.now().date().isoformat(),
            },
            format='json',
        )

        # Segundo usuario autenticado
        other_user_id = uuid.uuid4()
        other_client = APIClient()
        other_client.force_authenticate(user=SupabaseUser(id=str(other_user_id)))
        other_client.credentials(HTTP_AUTHORIZATION='Bearer another-token')

        snapshot_response = other_client.get(reverse('body-dashboard'))
        self.assertEqual(snapshot_response.status_code, 200, snapshot_response.data)
        self.assertEqual(snapshot_response.json()['activities'], [])
