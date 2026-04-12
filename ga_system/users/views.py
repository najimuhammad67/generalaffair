"""Views for the users app — login, logout, dashboard redirect, profile, user management."""

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from users.mixins import RoleRequiredMixin

from .forms import (
    AdminSetPasswordForm,
    ChangePasswordForm,
    LoginForm,
    ProfileForm,
    UserCreateForm,
)
from .models import User


class UserLoginView(auth_views.LoginView):
    """Custom login view with Bootstrap-styled form."""

    template_name = "users/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


class UserLogoutView(auth_views.LogoutView):
    """Logout and redirect to login page."""

    next_page = "users:login"


class DashboardRedirectView(LoginRequiredMixin, View):
    """Redirect user to the appropriate dashboard based on role."""

    def get(self, request):
        role = request.user.role
        if role in ("ga", "admin"):
            return redirect("requests_app:dashboard_ga")
        return redirect("requests_app:dashboard_employee")


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Allow any authenticated user to update their profile (name & phone)."""

    form_class = ProfileForm
    template_name = "users/profile.html"
    success_url = reverse_lazy("users:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profil berhasil diperbarui.")
        return super().form_valid(form)


class ChangePasswordView(LoginRequiredMixin, View):
    """Allow any user to change their own password (requires old password)."""

    def get(self, request):
        form = ChangePasswordForm()
        return render(request, "users/change_password.html", {"form": form})

    def post(self, request):
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            if not request.user.check_password(form.cleaned_data["old_password"]):
                form.add_error("old_password", "Password lama tidak benar.")
                return render(request, "users/change_password.html", {"form": form})
            request.user.set_password(form.cleaned_data["new_password"])
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Password berhasil diubah.")
            return redirect("users:profile")
        return render(request, "users/change_password.html", {"form": form})


# -------------------------------------------------------------------
# User Management (Admin only)
# -------------------------------------------------------------------


class UserListView(RoleRequiredMixin, ListView):
    """List all users with search and role filter."""

    allowed_roles = ["admin", "ga"]
    model = User
    template_name = "users/user_list.html"
    context_object_name = "users_list"
    paginate_by = 15

    def get_queryset(self):
        qs = super().get_queryset()

        # Filter by role
        role = self.request.GET.get("role")
        if role:
            qs = qs.filter(role=role)

        # Search
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(phone__icontains=q)
            )

        return qs.order_by("username")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role_choices"] = User.Role.choices
        ctx["current_role"] = self.request.GET.get("role", "")
        ctx["current_q"] = self.request.GET.get("q", "")
        return ctx


class UserCreateView(RoleRequiredMixin, CreateView):
    """Create a new user (GA only)."""

    allowed_roles = ["admin", "ga"]
    model = User
    form_class = UserCreateForm
    template_name = "users/user_form.html"
    success_url = reverse_lazy("users:user_list")

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'User "{user.username}" berhasil ditambahkan.')
        return redirect(self.success_url)


class UserUpdateView(RoleRequiredMixin, UpdateView):
    """Edit an existing user (GA only)."""

    allowed_roles = ["admin", "ga"]
    model = User
    template_name = "users/user_form.html"
    success_url = reverse_lazy("users:user_list")
    fields = ["username", "first_name", "last_name", "email", "role", "phone"]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Apply Bootstrap classes
        widget_map = {
            "username": {"class": "form-control"},
            "first_name": {"class": "form-control"},
            "last_name": {"class": "form-control"},
            "email": {"class": "form-control"},
            "role": {"class": "form-select"},
            "phone": {"class": "form-control"},
        }
        for field_name, attrs in widget_map.items():
            if field_name in form.fields:
                form.fields[field_name].widget.attrs.update(attrs)
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_edit"] = True
        ctx["edit_user"] = self.object
        return ctx

    def form_valid(self, form):
        user = form.save()
        messages.success(
            self.request, f'Data user "{user.username}" berhasil diperbarui.'
        )
        return redirect(self.success_url)


class AdminResetPasswordView(RoleRequiredMixin, View):
    """Admin resets a user's password (no old password needed)."""

    allowed_roles = ["admin", "ga"]

    def get(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        form = AdminSetPasswordForm()
        return render(
            request,
            "users/admin_reset_password.html",
            {
                "form": form,
                "target_user": target_user,
            },
        )

    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        form = AdminSetPasswordForm(request.POST)
        if form.is_valid():
            target_user.set_password(form.cleaned_data["new_password"])
            target_user.save()
            messages.success(
                request, f'Password user "{target_user.username}" berhasil direset.'
            )
            return redirect("users:user_list")
        return render(
            request,
            "users/admin_reset_password.html",
            {
                "form": form,
                "target_user": target_user,
            },
        )


class UserDeleteView(RoleRequiredMixin, View):
    """Delete a user (GA only). Cannot delete self."""

    allowed_roles = ["admin", "ga"]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "Anda tidak dapat menghapus akun Anda sendiri.")
            return redirect("users:user_list")
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" berhasil dihapus.')
        return redirect("users:user_list")
