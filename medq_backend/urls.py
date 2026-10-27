from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import views, status, permissions
from rest_framework.response import Response

from apps.accounts.views import (
    RegisterView,
    LoginView,
    DeliveryPersonnelListView,
    DeliveryPersonnelCountView,
    AdminUserListView,
    AdminUserDeleteView
)
from apps.orders.views import (
    OrderAssignDeliveryView,
    OrderRemoveDeliveryView,
    OrderStatusUpdateView,
    DeliveryAssignedOrdersView
)
from apps.products.models import Product
from apps.orders.models import Order
from apps.accounts.models import User


class AdminStatsView(views.APIView):
    """
    GET /api/admin/stats/
    Returns high-level analytics for the Admin dashboard.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_users = User.objects.filter(role=User.Role.CUSTOMER).count()
        total_orders = Order.objects.count()
        total_products = Product.objects.filter(is_active=True).count()
        total_delivery_boys = User.objects.filter(role=User.Role.DELIVERY_PERSON).count()
        low_stock = Product.objects.filter(is_active=True, stock_quantity__lt=5).count()
        
        from django.db.models import Sum
        completed_revenue = Order.objects.exclude(status=Order.Status.CANCELLED).aggregate(total=Sum('total_amount'))['total'] or 0

        return Response({
            "totalUsers": total_users,
            "totalOrders": total_orders,
            "totalProducts": total_products,
            "totalDeliveryBoys": total_delivery_boys,
            "lowStockCount": low_stock,
            "totalRevenue": float(completed_revenue)
        })


urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication & User Management
    path('api/auth/', include('apps.accounts.urls')),

    # Products & Categories
    path('api/', include('apps.products.urls')),

    # Cart
    path('api/cart/', include('apps.cart.urls')),

    # Orders
    path('api/orders/', include('apps.orders.urls')),

    # Contact & Feedback
    path('api/contact/', include('apps.feedback.urls')),
    path('api/feedback/', include('apps.feedback.urls')),

    # Delivery Boy Specific Endpoints (for legacy Spring Boot frontend compatibility)
    path('api/delivery/signup', RegisterView.as_view(), name='delivery_signup'),
    path('api/delivery/login', LoginView.as_view(), name='delivery_login'),
    path('api/delivery/all', DeliveryPersonnelListView.as_view(), name='delivery_all'),
    path('api/delivery/available', DeliveryPersonnelListView.as_view(), name='delivery_available'),
    path('api/delivery/total', DeliveryPersonnelCountView.as_view(), name='delivery_total'),
    path('api/delivery/assign', OrderAssignDeliveryView.as_view(), name='delivery_assign'),
    path('api/delivery/remove', OrderRemoveDeliveryView.as_view(), name='delivery_remove'),
    path('api/delivery/update-status/<int:id>', OrderStatusUpdateView.as_view(), name='delivery_update_status'),
    path('api/delivery/assigned-orders/<int:deliveryBoyId>', DeliveryAssignedOrdersView.as_view(), name='delivery_assigned_orders'),

    # Admin Dashboard Summary & Operations
    path('api/admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('api/admin/users/', AdminUserListView.as_view(), name='admin_users'),
    path('api/admin/users/<int:id>/', AdminUserDeleteView.as_view(), name='admin_user_delete'),
]

# Static & Media URL handling in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
