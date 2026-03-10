"""Unit tests for the notifications app."""

from unittest.mock import patch

from django.test import TestCase

from notifications.models import MessageTemplate, NotificationLog
from requests_app.models import ServiceRequest
from users.models import User


class MessageTemplateTest(TestCase):
    """Test dynamic message template rendering."""

    def setUp(self):
        MessageTemplate.objects.create(
            code="request_created",
            template_text="Halo GA, ada pengajuan baru dari {nama} kategori {kategori} di {lokasi}.",
            is_active=True,
        )
        MessageTemplate.objects.create(
            code="request_completed",
            template_text="Halo {nama}, pengajuan {kategori} telah selesai pada {tanggal}.",
            is_active=True,
        )
        MessageTemplate.objects.create(
            code="request_verified",
            template_text="Halo {nama}, pengajuan {kategori} di {lokasi} telah diverifikasi.",
            is_active=True,
        )
        MessageTemplate.objects.create(
            code="request_on_progress",
            template_text="Halo {nama}, pengajuan {kategori} di {lokasi} sedang diproses.",
            is_active=True,
        )
        MessageTemplate.objects.create(
            code="request_rejected",
            template_text="Halo {nama}, pengajuan {kategori} di {lokasi} ditolak.",
            is_active=True,
        )
        MessageTemplate.objects.create(
            code="manager_fyi",
            template_text="[INFO] Pengajuan #{request_id} ({kategori}) dari {nama} — status: {status}.",
            is_active=True,
        )
        MessageTemplate.objects.create(
            code="inactive_template",
            template_text="This should not render",
            is_active=False,
        )

    def test_render_template(self):
        from notifications.services import render_template

        result = render_template(
            "request_created",
            {
                "nama": "John",
                "kategori": "Maintenance",
                "lokasi": "Gedung A",
            },
        )
        self.assertIn("John", result)
        self.assertIn("Maintenance", result)
        self.assertIn("Gedung A", result)

    def test_render_completed_template(self):
        from notifications.services import render_template

        result = render_template(
            "request_completed",
            {
                "nama": "Jane",
                "kategori": "Cleaning",
                "tanggal": "04/03/2026 10:00",
            },
        )
        self.assertIn("Jane", result)
        self.assertIn("selesai", result)

    def test_render_verified_template(self):
        from notifications.services import render_template

        result = render_template(
            "request_verified",
            {
                "nama": "Budi",
                "kategori": "Supplies",
                "lokasi": "Gedung B",
            },
        )
        self.assertIn("Budi", result)
        self.assertIn("diverifikasi", result)

    def test_render_on_progress_template(self):
        from notifications.services import render_template

        result = render_template(
            "request_on_progress",
            {
                "nama": "Sari",
                "kategori": "Facility",
                "lokasi": "Lobby",
            },
        )
        self.assertIn("Sari", result)
        self.assertIn("diproses", result)

    def test_render_rejected_template(self):
        from notifications.services import render_template

        result = render_template(
            "request_rejected",
            {
                "nama": "Adi",
                "kategori": "Vehicle",
                "lokasi": "Parkir",
            },
        )
        self.assertIn("Adi", result)
        self.assertIn("ditolak", result)

    def test_render_manager_fyi_template(self):
        from notifications.services import render_template

        result = render_template(
            "manager_fyi",
            {
                "request_id": "42",
                "kategori": "Maintenance",
                "nama": "Dian",
                "status": "Verified",
            },
        )
        self.assertIn("#42", result)
        self.assertIn("Dian", result)
        self.assertIn("Verified", result)

    def test_inactive_template_returns_empty(self):
        from notifications.services import render_template

        result = render_template("inactive_template", {})
        self.assertEqual(result, "")

    def test_missing_template_returns_empty(self):
        from notifications.services import render_template

        result = render_template("nonexistent", {})
        self.assertEqual(result, "")


class NotificationLogTest(TestCase):
    """Test NotificationLog creation."""

    def test_create_log(self):
        user = User.objects.create_user(username="test", password="testpass123")
        sr = ServiceRequest.objects.create(
            requester=user,
            category="maintenance",
            description="Test",
            location="Test",
            urgency="low",
        )
        log = NotificationLog.objects.create(
            service_request=sr,
            recipient=user,
            message="Test message",
            status="sent",
            api_response='{"status": true}',
        )
        self.assertEqual(log.status, "sent")
        self.assertIn("Test message", log.message)


class NotifyManagersTest(TestCase):
    """Test the notify_managers helper function."""

    def setUp(self):
        self.manager = User.objects.create_user(
            username="mgr",
            password="testpass123",
            role="manager",
            phone="628111111111",
        )
        self.employee = User.objects.create_user(
            username="emp",
            password="testpass123",
            role="employee",
            phone="628222222222",
        )
        MessageTemplate.objects.create(
            code="manager_fyi",
            template_text="[INFO] Pengajuan #{request_id} ({kategori}) dari {nama} — status: {status}.",
            is_active=True,
        )

    @patch("notifications.services.send_whatsapp")
    def test_notify_managers_sends_to_all_managers(self, mock_send):
        mock_send.return_value = {"success": True}
        sr = ServiceRequest.objects.create(
            requester=self.employee,
            category="maintenance",
            description="AC bocor",
            location="Gedung A",
            urgency="high",
        )
        from notifications.services import notify_managers

        notify_managers(sr, "verified")

        # Should have called send_whatsapp for the manager
        mock_send.assert_called_once()
        call_args = mock_send.call_args
        self.assertEqual(call_args[0][0], "628111111111")
        self.assertIn("Maintenance", call_args[0][1])

    @patch("notifications.services.send_whatsapp")
    def test_notify_managers_skips_without_phone(self, mock_send):
        self.manager.phone = ""
        self.manager.save()

        sr = ServiceRequest.objects.create(
            requester=self.employee,
            category="cleaning",
            description="Test",
            location="Test",
            urgency="low",
        )
        from notifications.services import notify_managers

        notify_managers(sr, "verified")

        mock_send.assert_not_called()
