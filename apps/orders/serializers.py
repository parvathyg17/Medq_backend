from rest_framework import serializers
from .models import Order, OrderItem
from apps.accounts.serializers import UserProfileSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source='product_id', read_only=True)
    productName = serializers.CharField(source='product_name', read_only=True)
    productSku = serializers.CharField(source='product_sku', read_only=True)
    imageUrl = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    productImage = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = (
            'id', 'productId', 'product_name', 'productName',
            'product_sku', 'productSku', 'price', 'quantity', 'total_price',
            'imageUrl', 'image', 'productImage', 'product_image'
        )

    def get_imageUrl(self, obj):
        if obj.product:
            request = self.context.get('request')
            if obj.product.image:
                if request:
                    try:
                        return request.build_absolute_uri(obj.product.image.url)
                    except Exception:
                        pass
                url = obj.product.image.url
                if url.startswith('http://') or url.startswith('https://'):
                    return url
                return f"http://127.0.0.1:8000{url}"
            if obj.product.image_url:
                return obj.product.image_url
        return "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&auto=format&fit=crop&q=60"

    def get_image(self, obj):
        return self.get_imageUrl(obj)

    def get_productImage(self, obj):
        return self.get_imageUrl(obj)

    def get_product_image(self, obj):
        return self.get_imageUrl(obj)



class OrderSerializer(serializers.ModelSerializer):
    orderItems = OrderItemSerializer(source='order_items', many=True, read_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True)
    deliveryBoy = serializers.SerializerMethodField()
    delivery_boy_info = serializers.SerializerMethodField()

    # CamelCase aliases for frontend compatibility
    orderNumber = serializers.CharField(source='order_number', read_only=True)
    deliveryName = serializers.CharField(source='delivery_name', read_only=True)
    phoneNumber = serializers.CharField(source='phone_number', read_only=True)
    pinCode = serializers.CharField(source='pin_code', read_only=True)
    paymentMethod = serializers.CharField(source='payment_method', read_only=True)
    totalAmount = serializers.DecimalField(source='total_amount', max_digits=12, decimal_places=2, read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    returnReason = serializers.CharField(source='return_reason', read_only=True)
    returnAdminResponse = serializers.CharField(source='return_admin_response', read_only=True)
    returnRequestedAt = serializers.DateTimeField(source='return_requested_at', read_only=True)
    returnProcessedAt = serializers.DateTimeField(source='return_processed_at', read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'orderNumber', 'status',
            'delivery_name', 'deliveryName', 'email',
            'phone_number', 'phoneNumber', 'address',
            'landmark', 'pin_code', 'pinCode',
            'payment_method', 'paymentMethod', 'payment_status',
            'subtotal', 'shipping_fee', 'total_amount', 'totalAmount',
            'order_items', 'orderItems', 'deliveryBoy', 'delivery_boy_info',
            'return_reason', 'returnReason',
            'return_admin_response', 'returnAdminResponse',
            'return_requested_at', 'returnRequestedAt',
            'return_processed_at', 'returnProcessedAt',
            'created_at', 'createdAt', 'updated_at'
        )

    def get_deliveryBoy(self, obj):
        if obj.delivery_boy:
            return {
                'id': obj.delivery_boy.id,
                'name': obj.delivery_boy.full_name or obj.delivery_boy.username,
                'phone': obj.delivery_boy.phone or 'N/A',
                'email': obj.delivery_boy.email
            }
        return None

    def get_delivery_boy_info(self, obj):
        return self.get_deliveryBoy(obj)


class OrderCreateSerializer(serializers.Serializer):
    deliveryDetails = serializers.DictField(required=False)
    cartItems = serializers.ListField(required=False)
    paymentMethod = serializers.CharField(required=False, default='cod')
    paymentDetails = serializers.DictField(required=False, default=dict)

    # Direct top-level fields support
    delivery_name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone_number = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    landmark = serializers.CharField(required=False, allow_blank=True)
    pin_code = serializers.CharField(required=False)
    items = serializers.ListField(required=False)
