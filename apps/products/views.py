from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.permissions import IsAdminUserRole
from .models import Category, Product, WishlistItem
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductWriteSerializer,
    WishlistItemSerializer
)
from .filters import ProductFilter


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUserRole()]
        return [permissions.AllowAny()]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'brand', 'sku']
    ordering_fields = ['price', 'created_at', 'name', 'stock_quantity']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductWriteSerializer
        return ProductSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUserRole()]
        return [permissions.AllowAny()]

    def get_object(self):
        lookup = self.kwargs.get('pk')
        if lookup and not str(lookup).isdigit():
            return get_object_or_404(Product, slug=lookup)
        return super().get_object()

    def list(self, request, *args, **kwargs):
        # Allow disabling pagination if frontend explicitly requests all products
        if request.query_params.get('no_page') == 'true' or request.query_params.get('all') == 'true':
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='by-category')
    def by_category(self, request):
        category_name = request.query_params.get('category', '').strip()
        if not category_name or category_name.lower() == 'all':
            products = self.get_queryset()
        else:
            products = self.get_queryset().filter(
                models_q := (
                    models.Q(category__slug__iexact=category_name) |
                    models.Q(category__name__icontains=category_name)
                )
            )
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def count(self, request):
        return Response(self.get_queryset().count())

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_products = self.get_queryset().order_by('?')[:6]
        serializer = ProductSerializer(featured_products, many=True, context={'request': request})
        return Response(serializer.data)


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related('product', 'product__category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='add')
    def add_item(self, request):
        product_id = request.data.get('productId') or request.data.get('product_id')
        if not product_id:
            return Response({"error": "productId is required."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, pk=product_id)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='remove/(?P<product_id>[^/.]+)')
    def remove_item(self, request, product_id=None):
        deleted_count, _ = WishlistItem.objects.filter(user=request.user, product_id=product_id).delete()
        if deleted_count > 0:
            return Response({"message": "Item removed from wishlist."}, status=status.HTTP_200_OK)
        return Response({"message": "Item not found in wishlist."}, status=status.HTTP_404_NOT_FOUND)
