"""
Service layer for request management.
All status-change logic is centralised here, creating RequestLog entries
and keeping views clean.
"""

from django.db import transaction

from .models import RequestLog, ServiceRequest


# Valid status transitions: current_status → [allowed next statuses]
VALID_TRANSITIONS = {
    'pending': ['verified', 'rejected'],
    'verified': ['on_progress', 'rejected'],
    'on_progress': ['completed', 'rejected'],
    'rejected': [],       # terminal state
    'completed': [],      # terminal state
}


@transaction.atomic
def create_request(
    user,
    category: str,
    description: str,
    location: str,
    urgency: str,
    attachment = None,
) -> ServiceRequest:
    """Create a new ServiceRequest and return it."""
    sr = ServiceRequest.objects.create(
        requester=user,
        category=category,
        description=description,
        location=location,
        urgency=urgency,
        attachment=attachment,
        status=ServiceRequest.Status.PENDING,
    )
    return sr


@transaction.atomic
def update_status(
    service_request: ServiceRequest,
    new_status: str,
    updated_by,
    notes: str = '',
) -> RequestLog:
    """
    Change the status of a ServiceRequest and create an audit log entry.
    Validates the transition is allowed.
    Returns the newly created RequestLog.
    Raises ValueError if the transition is not valid.
    """
    old_status = service_request.status

    # Skip validation if status hasn't changed
    if old_status == new_status:
        raise ValueError(
            f'Status sudah {service_request.get_status_display()}. '
            f'Pilih status lain untuk mengupdate.'
        )

    # Validate transition
    allowed = VALID_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        old_display = service_request.get_status_display()
        new_display = dict(ServiceRequest.Status.choices).get(new_status, new_status)
        raise ValueError(
            f'Transisi status tidak valid: {old_display} → {new_display}. '
            f'Status yang diizinkan: {", ".join(allowed) or "tidak ada (terminal state)"}.'
        )

    service_request.status = new_status
    service_request.save(update_fields=['status'])

    log = RequestLog.objects.create(
        service_request=service_request,
        old_status=old_status,
        new_status=new_status,
        updated_by=updated_by,
        notes=notes,
    )
    return log
