"""
Django signals for automatic WhatsApp notifications.
- On new ServiceRequest → broadcast to all GA staff
- On status change to completed/rejected → notify the requester

All notifications are deferred via transaction.on_commit() so external
API calls never run inside an atomic block.
"""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import RequestLog, ServiceRequest


@receiver(post_save, sender=ServiceRequest)
def notify_ga_on_new_request(sender, instance, created, **kwargs):
    """When a new request is created, broadcast WA to all GA users."""
    if created:
        pk = instance.pk

        def _send():
            from notifications.services import broadcast_to_ga

            sr = ServiceRequest.objects.get(pk=pk)
            broadcast_to_ga(sr)

        transaction.on_commit(_send)


@receiver(post_save, sender=RequestLog)
def notify_requester_on_status_change(sender, instance, created, **kwargs):
    """When any status change occurs, notify the requester and managers."""
    if created:
        sr_pk = instance.service_request_id
        new_status = instance.new_status

        def _send():
            from notifications.services import notify_managers, notify_requester

            sr = ServiceRequest.objects.get(pk=sr_pk)
            notify_requester(sr, new_status)
            notify_managers(sr, new_status)

        transaction.on_commit(_send)
