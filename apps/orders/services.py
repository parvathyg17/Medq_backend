from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.products.models import Product
from apps.cart.models import Cart
from .models import Order, OrderItem


class OrderPlacementService:
    @staticmethod
    def create_order(user, data, session_key=None):
        """
        Executes an atomic checkout:
        1. Validates recipient and address fields.
        2. Resolves cart items.
        3. Locks product rows (select_for_update) to prevent race conditions.
        4. Validates stock availability.
        5. Computes authoritative server-side totals.
        6. Safely decrements stock.
        7. Creates Order and OrderItem records.
        8. Clears the shopping cart.
        """
        delivery_details = data.get('deliveryDetails', {})
        delivery_name = delivery_details.get('deliveryName') or data.get('delivery_name') or data.get('userName')
        email = delivery_details.get('email') or data.get('email') or data.get('userEmail')
        phone_number = delivery_details.get('phoneNumber') or data.get('phone_number') or data.get('userPhone')
        address = delivery_details.get('address') or data.get('address') or data.get('deliveryAddress')
        landmark = delivery_details.get('landmark') or data.get('landmark', '')
        pin_code = delivery_details.get('pinCode') or data.get('pin_code') or data.get('pinCode') or (address and address.split('-')[-1].strip() if '-' in address else None)
        payment_method = data.get('paymentMethod') or data.get('payment_method') or data.get('paymentMode', 'cod')
        payment_details = data.get('paymentDetails', {})

        if not delivery_name or not email or not phone_number or not address:
            raise ValidationError("Please provide complete delivery details: name, email, phone, and address.")

        # Determine item list
        raw_items = data.get('cartItems') or data.get('items')
        cart = None
        if user and user.is_authenticated:
            cart = Cart.objects.filter(user=user).first()
        elif session_key:
            cart = Cart.objects.filter(session_key=session_key).first()

        item_requests = []
        if raw_items:
            for it in raw_items:
                p_id = it.get('productId') or it.get('product_id') or it.get('id')
                qty = int(it.get('quantity', 1))
                if p_id and qty > 0:
                    item_requests.append({'product_id': p_id, 'quantity': qty})
        elif cart and cart.items.exists():
            for it in cart.items.all():
                item_requests.append({'product_id': it.product_id, 'quantity': it.quantity})

        if not item_requests:
            raise ValidationError("Cannot place an order with an empty cart.")

        # PCI compliance: mask card number
        masked_card = None
        card_num = payment_details.get('cardNumber', '')
        if card_num:
            clean_num = ''.join(c for c in card_num if c.isdigit())
            if len(clean_num) >= 4:
                masked_card = f"•••• •••• •••• {clean_num[-4:]}"

        with transaction.atomic():
            subtotal = Decimal('0.00')
            order_items_to_create = []

            for item_req in item_requests:
                product_id = item_req['product_id']
                qty = item_req['quantity']

                # Lock row for atomic inventory decrement
                try:
                    product = Product.objects.select_for_update().get(id=product_id, is_active=True)
                except Product.DoesNotExist:
                    raise ValidationError(f"Product ID {product_id} was not found or is no longer available.")

                if product.stock_quantity < qty:
                    raise ValidationError(
                        f"Insufficient stock for '{product.name}'. Requested: {qty}, Available: {product.stock_quantity}."
                    )

                # Authoritative pricing calculation
                unit_price = product.effective_price
                line_total = Decimal(qty) * unit_price
                subtotal += line_total

                # Decrement inventory safely
                product.stock_quantity -= qty
                product.save(update_fields=['stock_quantity'])

                order_items_to_create.append({
                    'product': product,
                    'product_name': product.name,
                    'product_sku': product.sku,
                    'price': unit_price,
                    'quantity': qty,
                    'total_price': line_total
                })

            shipping_fee = Decimal('0.00')
            total_amount = subtotal + shipping_fee

            # Create Order
            order = Order.objects.create(
                user=user if (user and user.is_authenticated) else None,
                delivery_name=delivery_name,
                email=email,
                phone_number=phone_number,
                address=address,
                landmark=landmark,
                pin_code=pin_code,
                payment_method=payment_method,
                payment_status=Order.PaymentStatus.COMPLETED if payment_method in ['creditCard', 'upi'] else Order.PaymentStatus.PENDING,
                masked_card_number=masked_card,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                status=Order.Status.CONFIRMED
            )

            # Bulk create order items
            for oi in order_items_to_create:
                OrderItem.objects.create(
                    order=order,
                    product=oi['product'],
                    product_name=oi['product_name'],
                    product_sku=oi['product_sku'],
                    price=oi['price'],
                    quantity=oi['quantity'],
                    total_price=oi['total_price']
                )

            # Clear cart
            if cart:
                cart.items.all().delete()

            # Optional: save address to user's saved addresses
            save_addr = delivery_details.get('saveAddress') or data.get('save_address')
            if save_addr and user and user.is_authenticated:
                from apps.accounts.models import Address
                make_default = bool(delivery_details.get('isDefault') or data.get('is_default'))
                Address.objects.create(
                    user=user,
                    full_name=delivery_name,
                    phone=phone_number,
                    address_line=address,
                    landmark=landmark or '',
                    pin_code=pin_code,
                    is_default=make_default
                )

            return order
