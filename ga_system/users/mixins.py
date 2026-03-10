"""
Mixins for role-based access control in class-based views.
Replaces the combination of @role_required decorator + LoginRequiredMixin.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin):
    """
    Mixin that restricts view access to users whose role is in
    ``allowed_roles``.  Inherits LoginRequiredMixin so there is
    no need to add it separately.

    Usage::

        class MyView(RoleRequiredMixin, TemplateView):
            allowed_roles = ['ga', 'manager']
    """

    allowed_roles: list[str] = []

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin.dispatch handles unauthenticated users
        response = super().dispatch(request, *args, **kwargs)

        # After LoginRequiredMixin, check role
        if request.user.is_authenticated and self.allowed_roles:
            if request.user.role not in self.allowed_roles:
                messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
                return redirect('users:dashboard')

        return response
