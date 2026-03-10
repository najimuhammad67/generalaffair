"""
Decorator for role-based access control.
Usage:
    @role_required('ga', 'manager')
    def my_view(request): ...
"""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*allowed_roles):
    """
    Restrict view access to users whose role is in *allowed_roles*.
    Unauthenticated users are sent to LOGIN_URL.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:login')
            if request.user.role not in allowed_roles:
                messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
                return redirect('users:dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
