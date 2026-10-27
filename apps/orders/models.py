import random
import string
from decimal import Decimal
from django.db import models
from django.conf import settings
from apps.products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED = 'shipped', 'Shipped'
        OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'
        RETURN_REQUESTED = 'return_requested', 'Return Requested'
        RETURNED = 'returned', 'Returned'
        RETURN_REJECTED = 'return_rejected', 'Return Rejected'

    class PaymentMethod(models.TextChoices):
        CREDIT_CARD = 'creditCard', 'Credit Card'
        UPI = 'upi', 'UPI Payment'
        COD = 'cod', 'Cash On Delivery'

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    order_number = models.CharField(max_length=40, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )

    # Customer & Delivery Details
    delivery_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=25)
    address = models.TextField()
    landmark = models.CharField(max_length=150, blank=True, null=True)
    pin_code = models.CharField(max_length=15)

    # Payment details (PCI compliant: masked/sanitized only)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    masked_card_number = models.CharField(max_length=20, blank=True, null=True)

    # Financials (Computed strictly server-side)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Fulfillment
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.CONFIRMED)
    delivery_boy = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_deliveries'
    )

    # Return Management
    return_reason = models.TextField(blank=True, null=True)
    return_admin_response = models.TextField(blank=True, null=True)
    return_requested_at = models.DateTimeField(blank=True, null=True)
    return_processed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            self.order_number = f"MEDQ-{chars}"
        super().save(*args, **kwargs)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.order_items.all())

    def __str__(self):
        return f"Order #{self.id} ({self.order_number}) - ₹{self.total_amount} [{self.status}]"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=60, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Unit price at time of purchase
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.price is not None:
            self.total_price = Decimal(str(self.quantity)) * Decimal(str(self.price))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product_name} @ ₹{self.price}"
