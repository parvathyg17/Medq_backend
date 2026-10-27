from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.products.models import Category, Product
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem

User = get_user_model()


class OrdersAndCartApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Therapeutic Equipment", slug="therapeutic")
        self.product = Product.objects.create(
            name="Clinical Ultrasonic Nebulizer",
            slug="ultrasonic-nebulizer",
            sku="THER-001",
            category=self.category,
            price=Decimal("1500.00"),
            stock_quantity=5,
            description="Nebulizer for clinic"
        )
        self.customer = User.objects.create_user(
            username='buyer@example.com',
            email='buyer@example.com',
            password='Password@123',
            role=User.Role.CUSTOMER
        )

    def test_cart_add_and_update(self):
        self.client.force_authenticate(user=self.customer)
        # Add 2 items
        add_res = self.client.post('/api/cart/add/', {"productId": self.product.id, "quantity": 2}, format='json')
        self.assertEqual(add_res.status_code, status.HTTP_200_OK)

        # Check cart
        cart_res = self.client.get('/api/cart/')
        self.assertEqual(cart_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(cart_res.data), 1)
        self.assertEqual(cart_res.data[0]['quantity'], 2)

    def test_cart_stock_exceeded_error(self):
        self.client.force_authenticate(user=self.customer)
        # Set product stock to 3 (below limit of 5)
        self.product.stock_quantity = 3
        self.product.save()
        # Try to add 4 items (within limit 5, but exceeds stock 3)
        res = self.client.post('/api/cart/add/', {"productId": self.product.id, "quantity": 4}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("available in stock", str(res.data))

    def test_cart_limit_5_units_error(self):
        self.client.force_authenticate(user=self.customer)
        self.product.stock_quantity = 20
        self.product.save()
        # Try to add 6 items (exceeds limit 5)
        res = self.client.post('/api/cart/add/', {"productId": self.product.id, "quantity": 6}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("limit of 5", str(res.data).lower())


    def test_order_creation_decrements_stock_and_computes_total(self):
        self.client.force_authenticate(user=self.customer)
        checkout_payload = {
            "deliveryDetails": {
                "deliveryName": "Buyer Name",
                "email": "buyer@example.com",
                "phoneNumber": "9998887776",
                "address": "123 Hospital Lane",
                "landmark": "Near Gate 1",
                "pinCode": "560002"
            },
            "cartItems": [
                {
                    "productId": self.product.id,
                    "quantity": 2,
                    # Frontend attempts to send fake price of 10.00, server must ignore it!
                    "price": 10.00
                }
            ],
            "paymentMethod": "cod"
        }

        response = self.client.post('/api/orders/confirm', checkout_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))

        # Check order total in DB (2 * 1500.00 = 3000.00, not 2 * 10.00)
        order = Order.objects.get(id=response.data['id'])
        self.assertEqual(order.total_amount, Decimal("3000.00"))

        # Check stock decremented from 5 to 3
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

    def test_order_insufficient_stock_fails_atomically(self):
        self.client.force_authenticate(user=self.customer)
        checkout_payload = {
            "deliveryDetails": {
                "deliveryName": "Buyer Name",
                "email": "buyer@example.com",
                "phoneNumber": "9998887776",
                "address": "123 Hospital Lane",
                "pinCode": "560002"
            },
            "cartItems": [
                {"productId": self.product.id, "quantity": 99}
            ]
        }
        response = self.client.post('/api/orders/confirm', checkout_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Ensure stock remained intact (5)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)

    def test_order_cancellation_restores_stock(self):
        self.client.force_authenticate(user=self.customer)
        checkout_payload = {
            "deliveryDetails": {
                "deliveryName": "Buyer Name",
                "email": "buyer@example.com",
                "phoneNumber": "9998887776",
                "address": "123 Hospital Lane",
                "pinCode": "560002"
            },
            "cartItems": [
                {"productId": self.product.id, "quantity": 2}
            ]
        }
        res = self.client.post('/api/orders/confirm', checkout_payload, format='json')
        order_id = res.data['id']

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

        # Now cancel order
        cancel_res = self.client.delete(f'/api/orders/{order_id}')
        self.assertEqual(cancel_res.status_code, status.HTTP_200_OK)

        # Check order status changed to cancelled
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.status, Order.Status.CANCELLED)

        # Check stock restored from 3 back to 5
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)
