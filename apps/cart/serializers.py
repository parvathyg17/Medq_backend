from decimal import Decimal
from rest_framework import serializers
from apps.products.serializers import ProductSerializer
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    productId = serializers.IntegerField(source='product.id', read_only=True)
    productName = serializers.CharField(source='product.name', read_only=True)
    productDescription = serializers.CharField(source='product.description', read_only=True)
    price = serializers.DecimalField(source='product.effective_price', max_digits=10, decimal_places=2, read_only=True)
    imageUrl = serializers.SerializerMethodField()
    category = serializers.CharField(source='product.category.name', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    stock_quantity = serializers.IntegerField(source='product.stock_quantity', read_only=True)

    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'product_id', 'productId', 'productName',
            'productDescription', 'price', 'imageUrl', 'category',
            'quantity', 'total_price', 'stock_quantity'
        )

    def get_imageUrl(self, obj):
        request = self.context.get('request')
        if obj.product.image:
            if request:
                return request.build_absolute_uri(obj.product.image.url)
            return obj.product.image.url
        return obj.product.image_url or "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&auto=format&fit=crop&q=60"


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    shipping_fee = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'items', 'total_items', 'subtotal', 'shipping_fee', 'total_amount', 'updated_at')
