"""
Test dashboard data - simulate GADashboardView
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ga_system.settings')
django.setup()

from requests_app.models import ServiceRequest
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

print("=" * 60)
print("Testing Dashboard Data - GADashboardView Simulation")
print("=" * 60)

# Base queryset (no date filter)
requests_qs = ServiceRequest.objects.all()

# Single aggregated query for all counts
counts = requests_qs.aggregate(
    total_all=Count("id"),
    total_pending=Count("id", filter=Q(status="pending")),
    total_on_progress=Count("id", filter=Q(status="on_progress")),
    total_completed=Count("id", filter=Q(status="completed")),
    total_rejected=Count("id", filter=Q(status="rejected")),
)

print("\nCounts:")
print(f"  total_all: {counts['total_all']}")
print(f"  total_pending: {counts['total_pending']}")
print(f"  total_on_progress: {counts['total_on_progress']}")
print(f"  total_completed: {counts['total_completed']}")
print(f"  total_rejected: {counts['total_rejected']}")

# Monthly data query
monthly_data_qs = requests_qs.annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    count=Count('id')
).order_by('-month')[:6]

print(f"\nMonthly data query result:")
for item in monthly_data_qs:
    print(f"  {item['month']}: {item['count']}")

# Build labels and data arrays (reverse to show oldest to newest)
monthly_labels = []
monthly_data = []
for item in reversed(list(monthly_data_qs)):
    if item['month']:
        label = item['month'].strftime('%Y-%m')
        monthly_labels.append(label)
        monthly_data.append(item['count'])

print(f"\nmonthly_labels (reversed): {monthly_labels}")
print(f"monthly_data (reversed): {monthly_data}")

# JavaScript format
print(f"\nJavaScript format for template:")
print(f"  monthly_labels: {monthly_labels}")
print(f"  monthly_data: {monthly_data}")
print(f"  total_pending: {counts['total_pending']}")
print(f"  total_on_progress: {counts['total_on_progress']}")
print(f"  total_completed: {counts['total_completed']}")
print(f"  total_rejected: {counts['total_rejected']}")
print(f"  total_all: {counts['total_all']}")

print("\n" + "=" * 60)
