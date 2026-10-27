from django.db.models import Q
import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(method='filter_category')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    brand = django_filters.CharFilter(field_name='brand', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price', 'in_stock', 'brand']

    def filter_category(self, queryset, name, value):
        if not value or value.lower() == 'all':
            return queryset
        return queryset.filter(
            Q(category__slug__iexact=value) |
            Q(category__name__icontains=value)
        )

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset
