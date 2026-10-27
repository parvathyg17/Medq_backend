from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Category, Product

User = get_user_model()


class ProductsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Diagnostic Equipment", slug="diagnostic")
        self.product = Product.objects.create(
            name="Digital Blood Pressure Monitor",
            slug="digital-bp-monitor",
            sku="DIAG-001",
            category=self.category,
            price=Decimal("2000.00"),
            stock_quantity=10,
            description="Accurate BP monitor"
        )
        self.customer = User.objects.create_user(
            username='cust@example.com', email='cust@example.com', password='Password@123', role=User.Role.CUSTOMER
        )
        self.admin = User.objects.create_user(
            username='admin@example.com', email='admin@example.com', password='AdminPassword@123', role=User.Role.ADMIN, is_staff=True
        )

    def test_product_list_public(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check either paginated or unpaginated
        results = response.data.get('results', response.data)
        self.assertTrue(len(results) >= 1)

    def test_product_filter_by_category(self):
        response = self.client.get('/api/products/?category=diagnostic')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertEqual(results[0]['name'], "Digital Blood Pressure Monitor")

    def test_customer_cannot_create_product(self):
        self.client.force_authenticate(user=self.customer)
        payload = {
            "name": "New ECG",
            "price": "5000.00",
            "stock_quantity": 5,
            "category": "Diagnostic Equipment",
            "description": "Unauthorized test"
        }
        response = self.client.post('/api/products/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_product(self):
        self.client.force_authenticate(user=self.admin)
        payload = {
            "name": "New Diagnostic Scanner",
            "price": "9500.00",
            "stock_quantity": 4,
            "category": "Diagnostic Equipment",
            "description": "Admin authorized test"
        }
        response = self.client.post('/api/products/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(name="New Diagnostic Scanner").exists())
