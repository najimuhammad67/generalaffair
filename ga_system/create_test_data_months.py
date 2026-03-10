"""
Script untuk membuat test data tersebar di beberapa bulan
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ga_system.settings')
django.setup()

from requests_app.models import ServiceRequest
from users.models import User
from django.utils import timezone
from datetime import timedelta, datetime, timezone as datetime_tz
import random

print("=" * 60)
print("Creating Test Data Spread Across 6 Months")
print("=" * 60)

# Clear existing
ServiceRequest.objects.all().delete()
print("Cleared existing requests...")

ga_user = User.objects.filter(role='ga').first()
employee_users = list(User.objects.filter(role='employee'))
if not employee_users:
    employee_users = [ga_user]

categories = ['maintenance', 'cleaning', 'security', 'supplies', 'vehicle', 'facility', 'other']
statuses = ['pending', 'verified', 'on_progress', 'completed', 'rejected']

now = timezone.now()
requests_to_create = []

# Create requests spread across 6 months (September 2025 to March 2026)
months_to_create = [
    (2025, 9),   # September 2025
    (2025, 10),  # October 2025
    (2025, 11),  # November 2025
    (2025, 12),  # December 2025
    (2026, 1),   # January 2026
    (2026, 2),   # February 2026
    (2026, 3),   # March 2026
]

for year, month in months_to_create:
    # Create about 8-12 requests per month
    num_requests = random.randint(8, 12)
    for i in range(num_requests):
        # Random day within the target month
        day = random.randint(1, 28)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)

        created_date = datetime(
            year, month, day, hour, minute,
            tzinfo=datetime_tz.utc
        )

        requests_to_create.append(ServiceRequest(
            requester=random.choice(employee_users),
            category=random.choice(categories),
            description=f'Request {year}-{month:02d} #{i+1}',
            location=f'Floor {random.randint(1, 5)}',
            urgency=random.choice(['low', 'medium', 'high', 'critical']),
            status=random.choice(statuses),
            created_at=created_date,
            updated_at=created_date,
        ))

ServiceRequest.objects.bulk_create(requests_to_create)

print(f"\nCreated {len(requests_to_create)} requests")

# Show breakdown by month
from django.db.models import Count
from django.db.models.functions import TruncMonth

monthly_summary = ServiceRequest.objects.annotate(
    month=TruncMonth('created_at')
).values('month').annotate(count=Count('id')).order_by('month')

print("\nRequests by month:")
for item in monthly_summary:
    print(f"  {item['month'].strftime('%Y-%m')}: {item['count']}")

# Show total
print(f"\nTotal requests: {ServiceRequest.objects.count()}")

# Show status breakdown
status_breakdown = ServiceRequest.objects.values('status').annotate(count=Count('id'))
print("\nStatus breakdown:")
for item in status_breakdown:
    print(f"  {item['status']}: {item['count']}")

print("=" * 60)
