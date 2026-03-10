"""
Custom User model with role-based access control.
Roles: employee, ga (General Affair staff), manager.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user with role and phone number for WhatsApp integration."""

    class Role(models.TextChoices):
        EMPLOYEE = 'employee', 'Employee'
        GA = 'ga', 'General Affair'
        MANAGER = 'manager', 'Manager'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Nomor WhatsApp, contoh: 6281234567890',
    )

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def is_ga(self):
        return self.role == self.Role.GA

    @property
    def is_manager(self):
        return self.role == self.Role.MANAGER
