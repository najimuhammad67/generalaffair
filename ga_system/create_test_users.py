"""
Script untuk membuat user test untuk GA System.
Jalankan dengan: python manage.py shell < create_test_users.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ga_system.settings')
django.setup()

from users.models import User

# Hapus user test jika sudah ada (opsional)
print("=" * 50)
print("Membuat User Test untuk GA System")
print("=" * 50)

# User GA (General Affair)
ga_user, created = User.objects.get_or_create(
    username='ga',
    defaults={
        'first_name': 'General',
        'last_name': 'Affair',
        'email': 'ga@gasystem.com',
        'role': 'ga',
        'phone': '6281234567801',
        'is_active': True
    }
)
if created:
    ga_user.set_password('Ga123456!')
    ga_user.save()
    print(f"✅ User GA dibuat: username='ga', password='Ga123456!'")
else:
    print(f"ℹ️  User GA sudah ada: username='ga'")

# User Employee
employee_user, created = User.objects.get_or_create(
    username='employee',
    defaults={
        'first_name': 'Karyawan',
        'last_name': 'Satu',
        'email': ' employee@gasystem.com',
        'role': 'employee',
        'phone': '6281234567803',
        'is_active': True
    }
)
if created:
    employee_user.set_password('Emp123456!')
    employee_user.save()
    print(f"✅ User Employee dibuat: username='employee', password='Emp123456!'")
else:
    print(f"ℹ️  User Employee sudah ada: username='employee'")

# User Employee 2
employee_user2, created = User.objects.get_or_create(
    username='dani',
    defaults={
        'first_name': 'Dani',
        'last_name': 'Putra',
        'email': 'dani@gasystem.com',
        'role': 'employee',
        'phone': '6289876543210',
        'is_active': True
    }
)
if created:
    employee_user2.set_password('Dani123456!')
    employee_user2.save()
    print(f"✅ User dibuat: username='dani', password='Dani123456!'")
else:
    print(f"ℹ️  User sudah ada: username='dani'")

print("=" * 50)
print("Selesai! Gunakan kredensial di atas untuk login.")
print("=" * 50)
