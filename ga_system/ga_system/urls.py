"""
URL configuration for ga_system project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from .views import LandingPageView

urlpatterns = [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls", namespace="users")),
    path("requests/", include("requests_app.urls", namespace="requests_app")),
    path("notifications/", include("notifications.urls", namespace="notifications")),
    path("", LandingPageView.as_view(), name="landing"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
