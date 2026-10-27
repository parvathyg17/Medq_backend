from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.products.models import Product


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=80, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        total = Decimal('0.00')
        for item in self.items.select_related('product'):
            total += Decimal(item.quantity) * item.product.effective_price
        return total

    @property
    def shipping_fee(self):
        # Free shipping for medical supplies
        return Decimal('0.00')

    @property
    def total_amount(self):
        return self.subtotal + self.shipping_fee

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.session_key})"
        return f"Cart of {owner} ({self.total_items} items)"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product')
        ordering = ['created_at']

    @property
    def total_price(self):
        return Decimal(self.quantity) * self.product.effective_price

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity > self.product.stock_quantity:
            raise ValidationError(f"Only {self.product.stock_quantity} units available in stock.")

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Cart #{self.cart.id}"
