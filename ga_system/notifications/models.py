"""
Models for WhatsApp notification templates and delivery logs.
"""

from django.conf import settings
from django.db import models


class MessageTemplate(models.Model):
    """
    Dynamic message templates using Python string .format() syntax.
    Available placeholders: {nama}, {kategori}, {status}, {tanggal}, {lokasi}, {deskripsi}
    """

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text='Kode unik, misal: request_created, request_completed',
    )
    template_text = models.TextField(
        help_text='Gunakan placeholder: {nama}, {kategori}, {status}, {tanggal}, {lokasi}',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Message Template'
        verbose_name_plural = 'Message Templates'

    def __str__(self):
        return self.code


class NotificationLog(models.Model):
    """Log of every WhatsApp notification attempt."""

    class DeliveryStatus(models.TextChoices):
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'

    service_request = models.ForeignKey(
        'requests_app.ServiceRequest',
        on_delete=models.CASCADE,
        related_name='notification_logs',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='notification_logs',
    )
    message = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=DeliveryStatus.choices,
    )
    api_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification Log'
        verbose_name_plural = 'Notification Logs'

    def __str__(self):
        return f'WA → {self.recipient} ({self.get_status_display()})'
