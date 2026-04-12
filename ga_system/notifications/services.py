import json
import logging
import requests
from django.conf import settings
from django.utils import timezone
from .models import MessageTemplate, NotificationLog

logger = logging.getLogger(__name__)

# URL Layanan Node.js (wa-service)
WA_SERVICE_URL = getattr(settings, "WA_SERVICE_URL", "http://localhost:3001/api/send")

def send_whatsapp_notification(phone, message, service_request=None, recipient=None):
    """
    Mengirim notifikasi WhatsApp via wa-service (Node.js).
    """
    if not phone:
        return {"success": False, "reason": "No phone number provided"}

    payload = {
        "phone": str(phone),
        "message": message
    }

    status = "failed"
    api_response = ""

    try:
        response = requests.post(WA_SERVICE_URL, json=payload, timeout=10)
        api_response = response.text
        result = response.json()
        
        if result.get('success'):
            logger.info(f"WhatsApp notification sent to {phone}")
            status = "sent"
        else:
            logger.warning(f"WhatsApp direct send failed for {phone}: {result.get('reason')}")
            
    except Exception as e:
        logger.error(f"Failed to connect to WA Service: {e}")
        api_response = str(e)
        result = {"success": False, "reason": str(e)}

    # Log to database if service_request and recipient are provided
    if service_request:
        NotificationLog.objects.create(
            service_request=service_request,
            recipient=recipient,
            message=message,
            status=status,
            api_response=api_response
        )

    return result

def render_template(code, context):
    """
    Render a MessageTemplate with the given context.
    """
    try:
        template = MessageTemplate.objects.get(code=code, is_active=True)
        return template.template_text.format(**context)
    except (MessageTemplate.DoesNotExist, KeyError, ValueError) as e:
        logger.error(f"Error rendering template {code}: {e}")
        return ""

def broadcast_to_ga(service_request):
    """
    Notify all GA staff about a new request.
    """
    from users.models import User
    ga_staff = User.objects.filter(role="ga", is_active=True)
    
    context = {
        "nama": service_request.requester.get_full_name() or service_request.requester.username,
        "kategori": service_request.get_category_display(),
        "lokasi": service_request.location,
        "deskripsi": service_request.description,
        "tanggal": service_request.created_at.strftime("%d/%m/%Y %H:i"),
    }
    
    message = render_template("request_created", context)
    if not message:
        return

    for staff in ga_staff:
        if staff.phone:
            send_whatsapp_notification(staff.phone, message, service_request, staff)

def notify_requester(service_request, status_code):
    """
    Notify the requester about status changes.
    """
    template_map = {
        "verified": "request_verified",
        "on_progress": "request_on_progress",
        "completed": "request_completed",
        "rejected": "request_rejected",
    }
    
    template_code = template_map.get(status_code)
    if not template_code:
        return

    context = {
        "nama": service_request.requester.get_full_name() or service_request.requester.username,
        "kategori": service_request.get_category_display(),
        "lokasi": service_request.location,
        "status": service_request.get_status_display(),
        "tanggal": timezone.now().strftime("%d/%m/%Y %H:i"),
    }
    
    message = render_template(template_code, context)
    if message and service_request.requester.phone:
        send_whatsapp_notification(service_request.requester.phone, message, service_request, service_request.requester)

def notify_managers(service_request, status_code):
    """
    Notify all managers about status changes.
    """
    from users.models import User
    managers = User.objects.filter(role="manager", is_active=True)
    
    context = {
        "nama": service_request.requester.get_full_name() or service_request.requester.username,
        "kategori": service_request.get_category_display(),
        "lokasi": service_request.location,
        "status": service_request.get_status_display(),
        "tanggal": timezone.now().strftime("%d/%m/%Y %H:i"),
    }
    
    message = render_template("manager_fyi", context)
    if not message:
        return

    for manager in managers:
        if manager.phone:
            send_whatsapp_notification(manager.phone, message, service_request, manager)

def notify_user_change(user, activity_type):
    """
    Legacy helper for user-related activity.
    """
    if not user.phone:
        return
        
    message = (
        f"*NOTIFIKASI SISTEM*\n\n"
        f"Halo {user.get_full_name() or user.username},\n"
        f"Ada aktivitas baru pada akun Anda: *{activity_type}*.\n\n"
        f"Terima kasih.\n"
        f"_GA System_"
    )
    
    return send_whatsapp_notification(user.phone, message)
