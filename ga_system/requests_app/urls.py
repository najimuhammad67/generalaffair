"""URL patterns for the requests app."""

from django.urls import path

from . import views

app_name = "requests_app"

urlpatterns = [
    # List & CRUD
    path("", views.RequestListView.as_view(), name="request_list"),
    path("create/", views.RequestCreateView.as_view(), name="request_create"),
    path("<int:pk>/", views.RequestDetailView.as_view(), name="request_detail"),
    path(
        "<int:pk>/update-status/",
        views.RequestUpdateStatusView.as_view(),
        name="request_update_status",
    ),
    path("<int:pk>/delete/", views.RequestDeleteView.as_view(), name="request_delete"),
    # Dashboards
    path(
        "dashboard/employee/",
        views.EmployeeDashboardView.as_view(),
        name="dashboard_employee",
    ),
    path("dashboard/ga/", views.GADashboardView.as_view(), name="dashboard_ga"),
]
