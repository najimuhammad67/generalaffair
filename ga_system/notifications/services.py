"""
Service layer for WhatsApp notifications via Baileys microservice.
Handles template rendering, API calls, and logging.
"""

import json
import logging
from string import Template
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.utils import timezone

from notifications.models import MessageTemplate, NotificationLog
from users.services import get_user_phone, get_users_by_role

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------


def render_template(code: str, context: dict) -> str:
    """
    Render a MessageTemplate identified by *code* using safe substitution.
    Uses string.Template to prevent format string injection.
    Returns empty string if template not found or inactive.
    """
    try:
        tpl = MessageTemplate.objects.get(code=code, is_active=True)
        # Convert {placeholder} to $placeholder for string.Template
        template_text = tpl.template_text
        for key in context:
            template_text = template_text.replace("{" + key + "}", "${" + key + "}")
        safe_tpl = Template(template_text)
        return safe_tpl.safe_substitute(context)
    except MessageTemplate.DoesNotExist:
        logger.warning('MessageTemplate "%s" not found or inactive.', code)
        return ""


# ---------------------------------------------------------------
# Baileys WhatsApp Service
# ---------------------------------------------------------------


def send_whatsapp(phone: str, message: str) -> dict:
    """
    Send a WhatsApp message via the local Baileys microservice.
    Uses stdlib urllib only (no third-party requests library needed).
    Returns dict with 'success' key.
    """
    service_url = getattr(settings, "WA_SERVICE_URL", "")
    api_key = getattr(settings, "WA_API_KEY", "")

    if not service_url:
        logger.warning("WA_SERVICE_URL is not configured — skipping WA send.")
        return {"success": False, "message": "WA_SERVICE_URL not configured"}

    payload = json.dumps({"phone": phone, "message": message}).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = Request(service_url, data=payload, headers=headers, method="POST")

    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        logger.error("WA Service error: %s", exc)
        return {"success": False, "message": str(exc)}
    except Exception as exc:
        logger.error("Unexpected WA error: %s", exc)
        return {"success": False, "message": str(exc)}


# ---------------------------------------------------------------
# High-level notification helpers
# ---------------------------------------------------------------


def _log_notification(service_request, recipient, message: str, api_response: dict):
    """Create a NotificationLog entry."""
    status = (
        NotificationLog.DeliveryStatus.SENT
        if api_response.get("success")
        else NotificationLog.DeliveryStatus.FAILED
    )
    NotificationLog.objects.create(
        service_request=service_request,
        recipient=recipient,
        message=message,
        status=status,
        api_response=str(api_response),
    )


def broadcast_to_ga(service_request) -> None:
    """Notify all GA staff about a new service request."""
    context = {
        "nama": service_request.requester.get_full_name()
        or service_request.requester.username,
        "kategori": service_request.get_category_display(),
        "status": service_request.get_status_display(),
        "tanggal": timezone.localtime(service_request.created_at).strftime(
            "%d/%m/%Y %H:%M"
        ),
        "lokasi": service_request.location,
        "deskripsi": service_request.description[:100],
        "request_id": str(service_request.pk),
    }
    message = render_template("request_created", context)
    if not message:
        return

    ga_users = get_users_by_role("ga")
    for user in ga_users:
        phone = get_user_phone(user)
        if phone:
            result = send_whatsapp(phone, message)
            _log_notification(service_request, user, message, result)


def notify_requester(service_request, new_status: str) -> None:
    """Notify the original requester about any status change."""
    template_code = f"request_{new_status}"
    context = {
        "nama": service_request.requester.get_full_name()
        or service_request.requester.username,
        "kategori": service_request.get_category_display(),
        "status": service_request.get_status_display(),
        "tanggal": timezone.now().strftime("%d/%m/%Y %H:%M"),
        "lokasi": service_request.location,
        "deskripsi": service_request.description[:100],
        "request_id": str(service_request.pk),
    }
    message = render_template(template_code, context)
    if not message:
        return

    phone = get_user_phone(service_request.requester)
    if phone:
        result = send_whatsapp(phone, message)
        _log_notification(service_request, service_request.requester, message, result)


def notify_managers(service_request, new_status: str) -> None:
    """Notify all Manager-role users about a status change (FYI reminder)."""
    context = {
        "nama": service_request.requester.get_full_name()
        or service_request.requester.username,
        "kategori": service_request.get_category_display(),
        "status": service_request.get_status_display(),
        "tanggal": timezone.now().strftime("%d/%m/%Y %H:%M"),
        "lokasi": service_request.location,
        "deskripsi": service_request.description[:100],
        "request_id": str(service_request.pk),
    }
    message = render_template("manager_fyi", context)
    if not message:
        return

    managers = get_users_by_role("manager")
    for user in managers:
        phone = get_user_phone(user)
        if phone:
            result = send_whatsapp(phone, message)
            _log_notification(service_request, user, message, result)
