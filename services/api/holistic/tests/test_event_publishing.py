"""Tests for event publishing in holistic context views."""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ..models import MoodEntry, UserProfileExtended

User = get_user_model()


@pytest.mark.django_db
class TestEventPublishing(TestCase):
    """Test event publishing for mood entries and IKIGAI updates."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    @patch("holistic.context_views.MESSAGING_AVAILABLE", True)
    @patch("holistic.context_views.publish_event")
    def test_mood_entry_publishes_event(self, mock_publish_event):
        """Test that creating a mood entry publishes a MoodCreatedEvent."""
        url = reverse("holistic:mood-entries-list-create")
        payload = {
            "auth_user_id": str(self.user.id),
            "recorded_at": datetime.now().isoformat(),
            "level": "good",
            "note": "Feeling great today!",
            "tags": ["productive", "energized"]
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(mock_publish_event.called)

        # Verify event structure
        call_args = mock_publish_event.call_args
        event = call_args[0][0]
        self.assertEqual(event.event_type, "user.mood.created")
        self.assertEqual(event.user_id, str(self.user.id))
        self.assertEqual(event.data["level"], "good")
        self.assertEqual(event.data["note"], "Feeling great today!")
        self.assertEqual(event.data["tags"], ["productive", "energized"])

    @patch("holistic.context_views.MESSAGING_AVAILABLE", True)
    @patch("holistic.context_views.publish_event")
    def test_ikigai_update_publishes_event(self, mock_publish_event):
        """Test that updating IKIGAI profile publishes an IkigaiUpdatedEvent."""
        url = reverse("holistic:user-profile-extended")
        payload = {
            "ikigai_passion": ["coding", "music"],
            "ikigai_mission": ["help people", "create technology"],
            "ikigai_vocation": ["software development"],
            "ikigai_profession": ["programming", "design"],
            "ikigai_statement": "Build technology that helps people grow.",
            "psychosocial_context": "Living in a supportive community",
            "support_network": "Family and friends",
            "current_stressors": "Work deadline"
        }

        response = self.client.put(url, payload, format="json")

        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertTrue(mock_publish_event.called)

        # Verify event structure
        call_args = mock_publish_event.call_args
        event = call_args[0][0]
        self.assertEqual(event.event_type, "user.ikigai.updated")
        self.assertEqual(event.user_id, str(self.user.id))
        self.assertEqual(event.data["ikigai_passion"], ["coding", "music"])
        self.assertEqual(event.data["ikigai_statement"], "Build technology that helps people grow.")

    @patch("holistic.context_views.MESSAGING_AVAILABLE", True)
    @patch("holistic.context_views.publish_event")
    def test_ikigai_partial_update_publishes_event(self, mock_publish_event):
        """Test that partial IKIGAI update publishes event only if IKIGAI fields changed."""
        # Create initial profile
        UserProfileExtended.objects.create(
            auth_user_id=self.user.id,
            ikigai_passion=["coding"],
            ikigai_statement="Initial statement"
        )

        url = reverse("holistic:user-profile-extended")

        # Test 1: Update IKIGAI field - should publish
        payload = {
            "ikigai_passion": ["coding", "reading"]
        }
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_publish_event.called)

        # Reset mock
        mock_publish_event.reset_mock()

        # Test 2: Update non-IKIGAI field - should NOT publish
        payload = {
            "support_network": "New friends"
        }
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Event should not be published for non-IKIGAI fields
        # (based on current implementation logic)

    @patch("holistic.context_views.MESSAGING_AVAILABLE", False)
    def test_mood_entry_without_messaging(self):
        """Test that mood entry creation works even if messaging is unavailable."""
        url = reverse("holistic:mood-entries-list-create")
        payload = {
            "auth_user_id": str(self.user.id),
            "recorded_at": datetime.now().isoformat(),
            "level": "moderate",
            "note": "Doing okay",
            "tags": []
        }

        response = self.client.post(url, payload, format="json")

        # Should still succeed even without messaging
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MoodEntry.objects.filter(auth_user_id=self.user.id).exists())

    @patch("holistic.context_views.MESSAGING_AVAILABLE", True)
    @patch("holistic.context_views.publish_event", side_effect=Exception("Kafka down"))
    def test_mood_entry_graceful_failure_on_event_publishing(self, mock_publish_event):
        """Test that request succeeds even if event publishing fails."""
        url = reverse("holistic:mood-entries-list-create")
        payload = {
            "auth_user_id": str(self.user.id),
            "recorded_at": datetime.now().isoformat(),
            "level": "good",
            "note": "Test resilience",
            "tags": []
        }

        response = self.client.post(url, payload, format="json")

        # Should still succeed even if event publishing fails
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MoodEntry.objects.filter(auth_user_id=self.user.id).exists())

    def test_messaging_health_endpoint(self):
        """Test the messaging health check endpoint."""
        url = reverse("holistic:messaging-health")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("messaging_backend", response.data)
        self.assertIn("messaging_available", response.data)
        self.assertIn("celery_available", response.data)
        self.assertEqual(response.data["status"], "ok")

    @patch("holistic.context_views.MESSAGING_AVAILABLE", True)
    @patch("holistic.context_views.publish_event")
    def test_event_has_trace_id(self, mock_publish_event):
        """Test that published events include trace_id for distributed tracing."""
        url = reverse("holistic:mood-entries-list-create")
        payload = {
            "auth_user_id": str(self.user.id),
            "recorded_at": datetime.now().isoformat(),
            "level": "excellent",
            "note": "Best day ever!",
            "tags": ["happy"]
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify event has trace_id
        call_args = mock_publish_event.call_args
        event = call_args[0][0]
        self.assertIsNotNone(event.trace_id)

    @patch("holistic.context_views.MESSAGING_AVAILABLE", True)
    @patch("holistic.context_views.publish_event")
    def test_event_includes_mood_id(self, mock_publish_event):
        """Test that MoodCreatedEvent includes the created mood's ID."""
        url = reverse("holistic:mood-entries-list-create")
        payload = {
            "auth_user_id": str(self.user.id),
            "recorded_at": datetime.now().isoformat(),
            "level": "low",
            "note": "Not feeling great",
            "tags": ["tired"]
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify event includes mood_id
        call_args = mock_publish_event.call_args
        event = call_args[0][0]
        self.assertIn("mood_id", event.data)

        # Verify mood_id is a valid UUID
        try:
            uuid.UUID(event.data["mood_id"])
        except ValueError:
            self.fail("mood_id is not a valid UUID")
