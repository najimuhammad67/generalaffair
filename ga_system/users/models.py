"""
Custom User model with role-based access control.
Roles: employee, ga (General Affair staff), manager.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extended user with role and phone number for WhatsApp integration."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        GA = 'ga', 'General Affair'
        KARYAWAN = 'karyawan', 'Karyawan'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.KARYAWAN,
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

    def save(self, *args, **kwargs):
        # Force superusers to have the 'admin' role
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    @property
    def is_ga(self):
        return self.role == self.Role.GA

    @property
    def is_karyawan(self):
        return self.role == self.Role.KARYAWAN

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN or self.is_superuser
