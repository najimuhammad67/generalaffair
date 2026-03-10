from django.apps import AppConfig


class RequestsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'requests_app'
    verbose_name = 'Service Requests'

    def ready(self):
        import requests_app.signals  # noqa: F401 — register signal handlers
