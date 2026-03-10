"""
Test script untuk memeriksa data dashboard
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ga_system.settings')
django.setup()

from requests_app.models import ServiceRequest
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone

print("=" * 60)
print("Testing Dashboard Data")
print("=" * 60)

# 1. Check total requests
total = ServiceRequest.objects.count()
print(f"\nTotal requests: {total}")

# 2. Check status counts
counts = ServiceRequest.objects.aggregate(
    total_all=Count("id"),
    total_pending=Count("id"),
    total_on_progress=Count("id"),
    total_completed=Count("id"),
    total_rejected=Count("id"),
)
print(f"\nStatus counts: {counts}")

# 3. Check monthly data using TruncMonth
monthly_data_qs = ServiceRequest.objects.annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    count=Count('id')
).order_by('-month')[:6]

print("\nMonthly data query:")
for item in monthly_data_qs:
    print(f"  Month: {item['month']}, Count: {item['count']}")

# 4. Build labels and data arrays (like in views.py)
monthly_labels = []
monthly_data = []
for item in reversed(list(monthly_data_qs)):
    if item['month']:
        label = item['month'].strftime('%Y-%m')
        monthly_labels.append(label)
        monthly_data.append(item['count'])

print(f"\nmonthly_labels: {monthly_labels}")
print(f"monthly_data: {monthly_data}")

# 5. Test JavaScript array format
print(f"\nJavaScript format for monthly_labels: {monthly_labels}")
print(f"JavaScript format for monthly_data: {monthly_data}")
