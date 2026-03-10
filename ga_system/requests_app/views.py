"""
Views for service requests.
All business logic is delegated to the service layer.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView, View

from users.mixins import RoleRequiredMixin

from .forms import ServiceRequestForm, StatusUpdateForm
from .models import ServiceRequest
from .services import create_request, update_status


# -------------------------------------------------------------------
# Request CRUD
# -------------------------------------------------------------------


class RequestListView(LoginRequiredMixin, ListView):
    """Paginated, filterable list of service requests."""

    model = ServiceRequest
    template_name = "requests_app/request_list.html"
    context_object_name = "requests"
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset().select_related("requester")
        user = self.request.user

        # Employees see only their own requests
        if user.role == "employee":
            qs = qs.filter(requester=user)

        # Filters
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        search = self.request.GET.get("q")
        if search:
            qs = qs.filter(
                Q(description__icontains=search) | Q(location__icontains=search)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ServiceRequest.Status.choices
        ctx["category_choices"] = ServiceRequest.Category.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["current_category"] = self.request.GET.get("category", "")
        ctx["current_q"] = self.request.GET.get("q", "")
        return ctx


class RequestCreateView(RoleRequiredMixin, CreateView):
    """Create a new service request. Only employees can create requests."""

    allowed_roles = ["employee"]
    model = ServiceRequest
    form_class = ServiceRequestForm
    template_name = "requests_app/request_form.html"

    def form_valid(self, form):
        sr = create_request(
            user=self.request.user,
            category=form.cleaned_data["category"],
            description=form.cleaned_data["description"],
            location=form.cleaned_data["location"],
            urgency=form.cleaned_data["urgency"],
            attachment=form.cleaned_data.get("attachment"),
        )
        messages.success(self.request, f"Pengajuan #{sr.pk} berhasil dibuat.")
        return redirect("requests_app:request_detail", pk=sr.pk)


class RequestDetailView(LoginRequiredMixin, DetailView):
    """Request detail with status timeline and update form (for GA/manager)."""

    model = ServiceRequest
    template_name = "requests_app/request_detail.html"
    context_object_name = "service_request"

    def get_queryset(self):
        qs = super().get_queryset().select_related("requester")
        user = self.request.user
        # Employees can only view their own requests
        if user.role == "employee":
            qs = qs.filter(requester=user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["logs"] = self.object.logs.select_related("updated_by").order_by(
            "-created_at"
        )
        if self.request.user.role in ("ga", "manager"):
            ctx["status_form"] = StatusUpdateForm()
        return ctx


class RequestUpdateStatusView(RoleRequiredMixin, View):
    """Handle status update form submission (GA / Manager only)."""

    allowed_roles = ["ga", "manager"]

    def post(self, request, pk):
        sr = get_object_or_404(ServiceRequest, pk=pk)
        form = StatusUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data["new_status"]
            try:
                update_status(
                    service_request=sr,
                    new_status=new_status,
                    updated_by=request.user,
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(
                    request,
                    f"Status pengajuan #{sr.pk} diubah menjadi {sr.get_status_display()}.",
                )
            except ValueError as exc:
                messages.error(request, str(exc))
        else:
            messages.error(request, "Form tidak valid.")
        return redirect("requests_app:request_detail", pk=pk)


class RequestDeleteView(RoleRequiredMixin, View):
    """Delete a service request (GA / Manager only)."""

    allowed_roles = ["ga", "manager"]

    def post(self, request, pk):
        sr = get_object_or_404(ServiceRequest, pk=pk)
        sr_pk = sr.pk
        sr.delete()
        messages.success(request, f"Pengajuan #{sr_pk} berhasil dihapus.")
        return redirect("requests_app:request_list")


# -------------------------------------------------------------------
# Dashboards
# -------------------------------------------------------------------


class EmployeeDashboardView(RoleRequiredMixin, TemplateView):
    """Dashboard for employees showing their own request stats."""

    allowed_roles = ["employee"]
    template_name = "requests_app/dashboard_employee.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Get date range filter from query params
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        # Base queryset for employee's requests
        user_requests = ServiceRequest.objects.filter(requester=self.request.user)

        # Apply date range filter if provided
        if date_from:
            try:
                from datetime import datetime
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                user_requests = user_requests.filter(created_at__date__gte=date_from)
            except ValueError:
                pass

        if date_to:
            try:
                from datetime import datetime, timedelta
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                # Include the entire day
                date_to = date_to + timedelta(days=1)
                user_requests = user_requests.filter(created_at__date__lt=date_to)
            except ValueError:
                pass

        # Single aggregated query instead of N+1
        counts = user_requests.aggregate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            verified=Count("id", filter=Q(status="verified")),
            on_progress=Count("id", filter=Q(status="on_progress")),
            rejected=Count("id", filter=Q(status="rejected")),
            completed=Count("id", filter=Q(status="completed")),
        )

        ctx["total_requests"] = counts["total"]
        ctx["recent_requests"] = user_requests[:5]
        ctx["status_counts"] = {
            "pending": counts["pending"],
            "verified": counts["verified"],
            "on_progress": counts["on_progress"],
            "rejected": counts["rejected"],
            "completed": counts["completed"],
        }
        ctx["date_from"] = self.request.GET.get('date_from', '')
        ctx["date_to"] = self.request.GET.get('date_to', '')
        return ctx


class GADashboardView(RoleRequiredMixin, TemplateView):
    """Dashboard for GA/Manager with aggregate stats and monthly chart data."""

    allowed_roles = ["ga", "manager"]
    template_name = "requests_app/dashboard_ga.html"

    def get_context_data(self, **kwargs):
        from datetime import datetime, timedelta

        ctx = super().get_context_data(**kwargs)

        # Get date range filter from query params
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        # Base queryset
        requests_qs = ServiceRequest.objects.all()

        # Apply date range filter if provided
        if date_from:
            try:
                date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
                requests_qs = requests_qs.filter(created_at__date__gte=date_from_dt)
            except ValueError:
                pass

        if date_to:
            try:
                date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
                # Include the entire day
                date_to_dt = date_to_dt + timedelta(days=1)
                requests_qs = requests_qs.filter(created_at__date__lt=date_to_dt)
            except ValueError:
                pass

        # Single aggregated query for all counts
        counts = requests_qs.aggregate(
            total_all=Count("id"),
            total_pending=Count("id", filter=Q(status="pending")),
            total_on_progress=Count("id", filter=Q(status="on_progress")),
            total_completed=Count("id", filter=Q(status="completed")),
            total_rejected=Count("id", filter=Q(status="rejected")),
        )
        ctx.update(counts)
        ctx["recent_requests"] = requests_qs.select_related(
            "requester"
        ).order_by("-created_at")[:5]

        # Optimized monthly data using single query with annotation
        # Use the same filtered queryset for consistency
        from django.db.models.functions import TruncMonth
        monthly_data_qs = requests_qs.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('-month')[:6]

        # Build labels and data arrays (reverse to show oldest to newest)
        monthly_labels = []
        monthly_data = []
        for item in reversed(list(monthly_data_qs)):
            if item['month']:
                label = item['month'].strftime('%Y-%m')
                monthly_labels.append(label)
                monthly_data.append(item['count'])

        # Fallback to empty arrays if no data
        if not monthly_labels:
            now = timezone.now()
            for i in range(5, -1, -1):
                from datetime import date
                month = now.month - i
                year = now.year
                if month <= 0:
                    month += 12
                    year -= 1
                label = f"{year}-{month:02d}"
                monthly_labels.append(label)
                monthly_data.append(0)

        ctx["monthly_labels"] = monthly_labels
        ctx["monthly_data"] = monthly_data
        ctx["date_from"] = self.request.GET.get('date_from', '')
        ctx["date_to"] = self.request.GET.get('date_to', '')
        return ctx
