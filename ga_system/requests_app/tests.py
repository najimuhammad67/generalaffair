"""Unit tests for the requests app."""

from unittest.mock import patch

from django.test import TestCase

from notifications.models import MessageTemplate
from users.models import User

from .models import RequestLog, ServiceRequest
from .services import create_request, update_status


class ServiceRequestModelTest(TestCase):
    """Tests for ServiceRequest and RequestLog models."""

    def setUp(self):
        self.employee = User.objects.create_user(
            username="emp",
            password="testpass123",
            role="employee",
        )
        self.ga_user = User.objects.create_user(
            username="ga",
            password="testpass123",
            role="ga",
        )

    def test_create_request_service(self):
        sr = create_request(
            user=self.employee,
            category="maintenance",
            description="AC rusak di ruang meeting",
            location="Gedung A Lt.2",
            urgency="high",
        )
        self.assertEqual(sr.status, "pending")
        self.assertEqual(sr.requester, self.employee)
        self.assertEqual(sr.category, "maintenance")

    def test_update_status_creates_log(self):
        sr = create_request(
            user=self.employee,
            category="cleaning",
            description="Perlu pembersihan",
            location="Lobby",
            urgency="low",
        )
        log = update_status(sr, "verified", self.ga_user, notes="Sudah dicek")
        sr.refresh_from_db()

        self.assertEqual(sr.status, "verified")
        self.assertIsInstance(log, RequestLog)
        self.assertEqual(log.old_status, "pending")
        self.assertEqual(log.new_status, "verified")
        self.assertEqual(log.updated_by, self.ga_user)
        self.assertEqual(log.notes, "Sudah dicek")

    def test_status_workflow_chain(self):
        sr = create_request(
            user=self.employee,
            category="supplies",
            description="Kertas habis",
            location="Office",
            urgency="medium",
        )
        update_status(sr, "verified", self.ga_user)
        update_status(sr, "on_progress", self.ga_user)
        update_status(sr, "completed", self.ga_user, notes="Selesai")

        sr.refresh_from_db()
        self.assertEqual(sr.status, "completed")
        self.assertEqual(sr.logs.count(), 3)

    def test_invalid_status_transition_raises(self):
        sr = create_request(
            user=self.employee,
            category="maintenance",
            description="Test invalid",
            location="Test",
            urgency="low",
        )
        # pending → completed is not a valid transition
        with self.assertRaises(ValueError):
            update_status(sr, "completed", self.ga_user)

    def test_str_representation(self):
        sr = create_request(
            user=self.employee,
            category="vehicle",
            description="Test",
            location="Parkiran",
            urgency="medium",
        )
        self.assertIn("Vehicle", str(sr))
        self.assertIn("Pending", str(sr))


class SignalNotificationTest(TestCase):
    """Test that signals fire notifications on all status changes."""

    def setUp(self):
        self.employee = User.objects.create_user(
            username="emp2",
            password="testpass123",
            role="employee",
            phone="628123456789",
        )
        self.ga_user = User.objects.create_user(
            username="ga2",
            password="testpass123",
            role="ga",
            phone="628987654321",
        )
        self.manager = User.objects.create_user(
            username="mgr2",
            password="testpass123",
            role="manager",
            phone="628555555555",
        )
        # Create templates needed by the signals
        for code in [
            "request_created",
            "request_verified",
            "request_on_progress",
            "request_completed",
            "request_rejected",
            "manager_fyi",
        ]:
            MessageTemplate.objects.create(
                code=code,
                template_text=f"Template {code}: {{nama}} {{kategori}} {{status}}",
                is_active=True,
            )

    @patch("notifications.services.send_whatsapp")
    def test_signal_fires_on_verified(self, mock_send):
        """Signal should trigger notification when status changes to verified."""
        mock_send.return_value = {"success": True}
        sr = create_request(
            user=self.employee,
            category="maintenance",
            description="Test verified notification",
            location="Gedung A",
            urgency="medium",
        )
        # Reset mock after creation (which triggers broadcast_to_ga)
        mock_send.reset_mock()

        update_status(sr, "verified", self.ga_user)

        # Should have been called for requester + manager
        self.assertTrue(mock_send.called)
        call_count = mock_send.call_count
        self.assertGreaterEqual(call_count, 1)

    @patch("notifications.services.send_whatsapp")
    def test_signal_fires_on_on_progress(self, mock_send):
        """Signal should trigger notification when status changes to on_progress."""
        mock_send.return_value = {"success": True}
        sr = create_request(
            user=self.employee,
            category="cleaning",
            description="Test on_progress notification",
            location="Lobby",
            urgency="low",
        )
        update_status(sr, "verified", self.ga_user)
        mock_send.reset_mock()

        update_status(sr, "on_progress", self.ga_user)

        self.assertTrue(mock_send.called)
