"""Admin registration for requests app."""

from django.contrib import admin

from .models import RequestLog, ServiceRequest


class RequestLogInline(admin.TabularInline):
    model = RequestLog
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'updated_by', 'notes', 'created_at')


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('pk', 'category', 'requester', 'status', 'urgency', 'created_at')
    list_filter = ('status', 'category', 'urgency')
    search_fields = ('description', 'location', 'requester__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [RequestLogInline]


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ('service_request', 'old_status', 'new_status', 'updated_by', 'created_at')
    list_filter = ('new_status',)
    readonly_fields = ('created_at',)
