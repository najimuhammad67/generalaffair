"""
Models for General Affair service requests and tracking log.
"""

from django.conf import settings
from django.db import models


class ServiceRequest(models.Model):
    """A request submitted by an employee for GA services."""

    class Category(models.TextChoices):
        MAINTENANCE = 'maintenance', 'Maintenance'
        CLEANING = 'cleaning', 'Cleaning'
        SECURITY = 'security', 'Security'
        SUPPLIES = 'supplies', 'Office Supplies'
        VEHICLE = 'vehicle', 'Vehicle'
        FACILITY = 'facility', 'Facility'
        OTHER = 'other', 'Other'

    class Urgency(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        ON_PROGRESS = 'on_progress', 'On Progress'
        REJECTED = 'rejected', 'Rejected'
        COMPLETED = 'completed', 'Completed'

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_requests',
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
    )
    description = models.TextField()
    location = models.CharField(max_length=255)
    urgency = models.CharField(
        max_length=20,
        choices=Urgency.choices,
        default=Urgency.MEDIUM,
    )
    attachment = models.FileField(
        upload_to='attachments/%Y/%m/',
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['-created_at']  # Newest requests first
        verbose_name = 'Service Request'
        verbose_name_plural = 'Service Requests'

    def __str__(self):
        return f'#{self.pk} — {self.get_category_display()} ({self.get_status_display()})'


class RequestLog(models.Model):
    """
    Audit trail for every status change on a ServiceRequest.
    Displayed as a timeline on the request detail page.
    """

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='logs',
    )
    old_status = models.CharField(max_length=20, choices=ServiceRequest.Status.choices)
    new_status = models.CharField(max_length=20, choices=ServiceRequest.Status.choices)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Request Log'
        verbose_name_plural = 'Request Logs'

    def __str__(self):
        return (
            f'Request #{self.service_request_id}: '
            f'{self.get_old_status_display()} → {self.get_new_status_display()}'
        )
