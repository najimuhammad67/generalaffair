"""Admin registration for notifications app."""

from django.contrib import admin

from .models import MessageTemplate, NotificationLog


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'is_active', 'template_text')
    list_filter = ('is_active',)
    search_fields = ('code', 'template_text')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'recipient', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('created_at',)
