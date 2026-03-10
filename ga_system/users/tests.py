"""Unit tests for the users app."""

from django.test import TestCase

from .models import User


class UserModelTest(TestCase):
    """Tests for the custom User model."""

    def test_create_employee(self):
        user = User.objects.create_user(
            username='employee1',
            password='testpass123',
            role=User.Role.EMPLOYEE,
            phone='6281234567890',
        )
        self.assertEqual(user.role, 'employee')
        self.assertTrue(user.is_employee)
        self.assertFalse(user.is_ga)
        self.assertFalse(user.is_manager)

    def test_create_ga_user(self):
        user = User.objects.create_user(
            username='ga1',
            password='testpass123',
            role=User.Role.GA,
        )
        self.assertEqual(user.role, 'ga')
        self.assertTrue(user.is_ga)

    def test_create_manager(self):
        user = User.objects.create_user(
            username='manager1',
            password='testpass123',
            role=User.Role.MANAGER,
        )
        self.assertTrue(user.is_manager)

    def test_default_role_is_employee(self):
        user = User.objects.create_user(username='default_user', password='testpass123')
        self.assertEqual(user.role, 'employee')

    def test_str_representation(self):
        user = User.objects.create_user(
            username='john',
            first_name='John',
            last_name='Doe',
            password='testpass123',
            role=User.Role.GA,
        )
        self.assertIn('John Doe', str(user))
        self.assertIn('General Affair', str(user))
