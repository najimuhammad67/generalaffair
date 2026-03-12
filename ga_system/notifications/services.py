import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# URL Layanan Node.js (wa-service)
WA_SERVICE_URL = "http://localhost:3001/api/send"

def send_whatsapp_notification(phone, message):
    """
    Mengirim notifikasi WhatsApp via wa-service (Node.js).
    Jika gagal kirim langsung, akan mengembalikan status dan link wa.me
    """
    if not phone:
        return {"success": False, "reason": "No phone number provided"}

    payload = {
        "phone": str(phone),
        "message": message
    }

    try:
        response = requests.post(WA_SERVICE_URL, json=payload, timeout=10)
        result = response.json()
        
        if result.get('success'):
            logger.info(f"WhatsApp notification sent to {phone} via Baileys")
        else:
            logger.warning(f"WhatsApp direct send failed for {phone}: {result.get('reason')}")
            
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to WA Service: {e}")
        # Jika service mati, kembalikan fallback manual
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        if clean_phone.startswith('0'):
            clean_phone = '62' + clean_phone[1:]
        return {
            "success": False, 
            "method": "fallback", 
            "link": f"https://wa.me/{clean_phone}",
            "reason": "WA Service is offline"
        }

def notify_user_change(user, activity_type):
    """
    Contoh penggunaan fungsi notifikasi saat ada perubahan data user.
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