"""
Middleware that injects user role into every request for easy access
in templates and views.
"""

from django.utils.deprecation import MiddlewareMixin


class RoleMiddleware(MiddlewareMixin):
    """Adds ``request.user_role`` with the current user's role string."""

    def process_request(self, request):
        if request.user.is_authenticated:
            request.user_role = request.user.role
        else:
            request.user_role = None
