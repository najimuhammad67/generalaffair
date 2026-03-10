"""
Service layer for user-related business logic.
Keeps views thin — all logic lives here.
"""

from django.db.models import QuerySet

from .models import User


def get_users_by_role(role: str) -> QuerySet[User]:
    """Return all active users with the given role."""
    return User.objects.filter(role=role, is_active=True)


def get_user_phone(user: User) -> str:
    """Return the user's WhatsApp-ready phone number or empty string."""
    return user.phone.strip() if user.phone else ''
