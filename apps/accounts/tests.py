from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class AccountsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            username='user@example.com',
            email='user@example.com',
            password='Password@123',
            role=User.Role.CUSTOMER
        )
        self.admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='AdminPassword@123',
            role=User.Role.ADMIN,
            is_staff=True
        )

    def test_customer_registration(self):
        payload = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "9123456789",
            "password": "SecurePassword@123",
            "confirm_password": "SecurePassword@123"
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='jane@example.com').exists())

    def test_registration_password_mismatch(self):
        payload = {
            "name": "Mismatched",
            "email": "mismatch@example.com",
            "phone": "9123456780",
            "password": "Password123",
            "confirm_password": "DifferentPassword123"
        }
        response = self.client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        payload = {
            "identifier": "user@example.com",
            "password": "Password@123"
        }
        response = self.client.post('/api/auth/login/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['role'], 'CUSTOMER')

    def test_login_invalid_credentials(self):
        payload = {
            "identifier": "user@example.com",
            "password": "WrongPassword"
        }
        response = self.client.post('/api/auth/login/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_current_user_profile_requires_auth(self):
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_profile_authenticated(self):
        self.client.force_authenticate(user=self.customer)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'user@example.com')
