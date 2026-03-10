"""Views for the notifications app."""

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.views.generic import ListView, TemplateView

from users.mixins import RoleRequiredMixin

from .models import NotificationLog


class NotificationLogListView(RoleRequiredMixin, ListView):
    """Paginated list of all WhatsApp notification logs (GA/Manager only)."""

    allowed_roles = ["ga", "manager"]
    model = NotificationLog
    template_name = "notifications/log_list.html"
    context_object_name = "logs"
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related("service_request", "recipient")


class WhatsAppDashboardView(RoleRequiredMixin, TemplateView):
    """Dashboard for monitoring WhatsApp service connection and QR pairing."""

    allowed_roles = ["ga", "manager"]
    template_name = "notifications/wa_dashboard.html"

    def _wa_service_url(self, endpoint: str) -> str:
        base = getattr(
            settings, "WA_SERVICE_URL", "http://localhost:3001/api/send-message"
        )
        # Derive the base URL from send-message endpoint
        return base.rsplit("/", 1)[0] + "/" + endpoint

    def _get_wa_status(self) -> dict:
        """Hit the wa-service /api/status endpoint."""
        try:
            url = self._wa_service_url("status")
            req = Request(url, method="GET")
            with urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (URLError, Exception):
            return {"connected": False, "qrPending": False, "serviceDown": True}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        status = self._get_wa_status()
        ctx["wa_connected"] = status.get("connected", False)
        ctx["wa_qr_pending"] = status.get("qrPending", False)
        ctx["wa_service_down"] = status.get("serviceDown", False)
        ctx["wa_qr_url"] = self._wa_service_url("qr")

        # Recent notification stats
        total = NotificationLog.objects.count()
        sent = NotificationLog.objects.filter(status="sent").count()
        failed = NotificationLog.objects.filter(status="failed").count()
        ctx["total_notifications"] = total
        ctx["sent_notifications"] = sent
        ctx["failed_notifications"] = failed
        ctx["recent_logs"] = NotificationLog.objects.select_related(
            "service_request", "recipient"
        ).order_by("-created_at")[:10]
        return ctx
