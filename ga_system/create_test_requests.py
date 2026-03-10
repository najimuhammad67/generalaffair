"""
Script untuk membuat test data untuk dashboard
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ga_system.settings')
django.setup()

from requests_app.models import ServiceRequest
from users.models import User
from django.utils import timezone
from datetime import timedelta, date
import random

print("=" * 60)
print("Creating Test Data for Dashboard")
print("=" * 60)

# Get users
ga_user = User.objects.filter(role='ga').first()
manager_user = User.objects.filter(role='manager').first()
employee_users = User.objects.filter(role='employee')

if not employee_users.exists():
    print("Warning: No employee users found!")

# Delete existing test requests (optional)
# ServiceRequest.objects.all().delete()
# print("Cleared existing requests...")

# Define categories and statuses
categories = ['maintenance', 'cleaning', 'security', 'supplies', 'vehicle', 'facility', 'other']

statuses = ['pending', 'verified', 'on_progress', 'completed', 'rejected']

# Create requests for the last 6 months
now = timezone.now()
created_count = 0
for i in range(100):
    # Random date within last 6 months
    days_ago = random.randint(0, 180)
    created_date = now - timedelta(days=days_ago)

    # Get random requester
    requester = employee_users.first() if employee_users.exists() else ga_user

    # Create request
    request, created = ServiceRequest.objects.get_or_create(
        defaults={
            'requester': requester,
            'category': random.choice(categories),
            'description': f'Test request #{i+1} with days_ago={days_ago}',
            'location': f'Office Floor {random.randint(1, 5)}',
            'urgency': random.choice(['low', 'medium', 'high', 'critical']),
            'status': random.choice(statuses),
            'created_at': created_date,
            'updated_at': created_date,
        }
    )
    if created:
        created_count += 1

print(f"\nCreated {created_count} new requests")
print(f"Total requests in database: {ServiceRequest.objects.count()}")
print("=" * 60)
