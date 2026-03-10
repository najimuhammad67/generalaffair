"""
Debug script untuk memeriksa tanggal
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ga_system.settings')
django.setup()

from requests_app.models import ServiceRequest
from users.models import User
from django.utils import timezone
from datetime import datetime, timezone as datetime_tz
import random

print("=" * 60)
print("Debugging Date Creation")
print("=" * 60)

# Current time
now = timezone.now()
print(f"Current timezone.now(): {now}")
print(f"Current timezone: {timezone.get_current_timezone()}")

# Try creating a date in different month
test_dates = [
    datetime(2025, 9, 15, 10, 30, tzinfo=datetime_tz.utc),
    datetime(2025, 10, 15, 10, 30, tzinfo=datetime_tz.utc),
    datetime(2026, 2, 15, 10, 30, tzinfo=datetime_tz.utc),
]

print("\nTest dates:")
for dt in test_dates:
    print(f"  {dt} -> month: {dt.month}, year: {dt.year}")

# Clear and create test requests
ServiceRequest.objects.all().delete()

ga_user = User.objects.filter(role='ga').first() or User.objects.first()

for i, dt in enumerate(test_dates):
    req = ServiceRequest.objects.create(
        requester=ga_user,
        category='maintenance',
        description=f'Test request #{i+1}',
        location='Floor 1',
        urgency='medium',
        status='pending',
        created_at=dt,
        updated_at=dt,
    )
    print(f"Created request #{i+1} with created_at stored: {req.created_at}")

# Check what's stored
print("\nStored in database:")
for req in ServiceRequest.objects.all():
    print(f"  #{req.pk}: {req.created_at} (month={req.created_at.month}, year={req.created_at.year})")

# Check TruncMonth query
from django.db.models import Count
from django.db.models.functions import TruncMonth

monthly = ServiceRequest.objects.annotate(
    month=TruncMonth('created_at')
).values('month').annotate(count=Count('id')).order_by('month')

print("\nTruncMonth results:")
for item in monthly:
    print(f"  {item['month']} (month={item['month'].month}, year={item['month'].year}): count={item['count']}")
