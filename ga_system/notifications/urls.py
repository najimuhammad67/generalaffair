"""URL patterns for the notifications app."""

from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("logs/", views.NotificationLogListView.as_view(), name="log_list"),
    path("wa-dashboard/", views.WhatsAppDashboardView.as_view(), name="wa_dashboard"),
]
