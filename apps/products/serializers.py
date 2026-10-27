from rest_framework import serializers
from .models import Category, Product, WishlistItem


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source='products.count', read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'is_active', 'product_count')


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    effective_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)

    # Aliases for frontend backward compatibility
    quantity = serializers.IntegerField(source='stock_quantity', read_only=True)
    imageUrl = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'sku', 'description', 'brand',
            'category', 'category_name', 'category_slug',
            'price', 'discount_price', 'effective_price',
            'stock_quantity', 'quantity', 'in_stock',
            'image', 'image_url', 'imageUrl', 'is_active',
            'created_at', 'updated_at'
        )

    def get_imageUrl(self, obj):
        request = self.context.get('request')
        if obj.image:
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        if obj.image_url:
            return obj.image_url
        return "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&auto=format&fit=crop&q=60"


class ProductWriteSerializer(serializers.ModelSerializer):
    category = serializers.CharField(required=True)
    quantity = serializers.IntegerField(source='stock_quantity', required=False)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'description', 'brand', 'category',
            'price', 'discount_price', 'stock_quantity', 'quantity',
            'image', 'image_url', 'is_active'
        )

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_category(self, value):
        # Resolve category by id, slug, or name
        if isinstance(value, Category):
            return value
        cat = Category.objects.filter(name__iexact=str(value)).first() or \
              Category.objects.filter(slug__iexact=str(value)).first() or \
              Category.objects.filter(id__iexact=str(value) if str(value).isdigit() else 0).first()
        if not cat:
            cat = Category.objects.create(name=str(value).strip())
        return cat

    def create(self, validated_data):
        category = validated_data.pop('category')
        return Product.objects.create(category=category, **validated_data)

    def update(self, instance, validated_data):
        if 'category' in validated_data:
            instance.category = validated_data.pop('category')
        return super().update(instance, validated_data)


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_id', 'created_at')
        read_only_fields = ('id', 'created_at')
