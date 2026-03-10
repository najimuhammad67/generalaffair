"""
Script untuk membuat test data bulk untuk dashboard
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ga_system.settings')
django.setup()

from requests_app.models import ServiceRequest
from users.models import User
from django.utils import timezone
from datetime import timedelta
import random

# Disable signals to avoid WA notification errors
from django.db.models.signals import pre_save, post_save

print("=" * 60)
print("Creating Test Data for Dashboard")
print("=" * 60)

ga_user = User.objects.filter(role='ga').first()
manager_user = User.objects.filter(role='manager').first()
employee_users = list(User.objects.filter(role='employee'))

if not employee_users:
    print("Warning: No employee users found! Using GA user as requester.")
    employee_users = [ga_user]

# Clear existing requests
ServiceRequest.objects.all().delete()
print("Cleared existing requests...")

# Define categories and statuses
categories = ['maintenance', 'cleaning', 'security', 'supplies', 'vehicle', 'facility', 'other']
statuses = ['pending', 'verified', 'on_progress', 'completed', 'rejected']

# Create requests for the last 6 months
now = timezone.now()
requests_to_create = []

for i in range(50):
    # Random date within last 6 months
    days_ago = random.randint(0, 180)
    created_date = now - timedelta(days=days_ago)

    # Get random requester
    requester = random.choice(employee_users)

    requests_to_create.append(ServiceRequest(
        requester=requester,
        category=random.choice(categories),
        description=f'Test request #{i+1} - {categories[random.randint(0, len(categories)-1)]}',
        location=f'Office Floor {random.randint(1, 5)}',
        urgency=random.choice(['low', 'medium', 'high', 'critical']),
        status=random.choice(statuses),
        created_at=created_date,
        updated_at=created_date,
    ))

# Bulk create
ServiceRequest.objects.bulk_create(requests_to_create)

print(f"\nCreated {len(requests_to_create)} requests")
print(f"Total requests in database: {ServiceRequest.objects.count()}")

# Show breakdown by status
from django.db.models import Count
status_counts = ServiceRequest.objects.values('status').annotate(count=Count('id'))
print("\nBreakdown by status:")
for item in status_counts:
    print(f"  {item['status']}: {item['count']}")

print("=" * 60)
