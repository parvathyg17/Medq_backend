from django.urls import path
from .views import (
    OrderConfirmView,
    OrderListView,
    OrderDetailView,
    OrderCancelView,
    OrderReturnView,
    AdminReturnListView,
    AdminApproveReturnView,
    AdminRejectReturnView,
    OrderAssignDeliveryView,
    OrderRemoveDeliveryView,
    OrderStatusUpdateView,
    OrderTotalCountView,
    DeliveryAssignedOrdersView
)

urlpatterns = [
    # Checkout & Confirmation
    path('confirm', OrderConfirmView.as_view(), name='order_confirm_legacy'),
    path('confirm/', OrderConfirmView.as_view(), name='order_confirm'),
    path('', OrderListView.as_view(), name='order_list'),
    path('all', OrderListView.as_view(), name='order_all_legacy'),
    path('all/', OrderListView.as_view(), name='order_all'),
    path('total', OrderTotalCountView.as_view(), name='order_total_legacy'),
    path('total/', OrderTotalCountView.as_view(), name='order_total'),

    # Returns Management (Dedicated Admin and Customer Endpoints)
    path('returns/', AdminReturnListView.as_view(), name='admin_returns_list'),
    path('returns', AdminReturnListView.as_view(), name='admin_returns_list_legacy'),
    path('<int:id>/return/approve/', AdminApproveReturnView.as_view(), name='admin_return_approve'),
    path('<int:id>/return/reject/', AdminRejectReturnView.as_view(), name='admin_return_reject'),

    # Detail, Tracking, Cancel & Return
    path('cancel-order/<int:id>', OrderCancelView.as_view(), name='order_cancel_alt_legacy'),
    path('cancel-order/<int:id>/', OrderCancelView.as_view(), name='order_cancel_alt'),
    path('<int:id>/status/', OrderStatusUpdateView.as_view(), name='order_status_update'),
    path('<int:id>/return/', OrderReturnView.as_view(), name='order_return'),
    path('return/<int:id>/', OrderReturnView.as_view(), name='order_return_alt'),
    path('track/<str:lookup>/', OrderDetailView.as_view(), name='order_track_lookup'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('<int:id>', OrderCancelView.as_view(), name='order_cancel_legacy'),
    path('<str:lookup>/', OrderDetailView.as_view(), name='order_detail_lookup'),

    # Delivery Assignment Stubs (for graceful legacy compatibility)
    path('assign', OrderAssignDeliveryView.as_view(), name='order_assign_legacy'),
    path('assign/', OrderAssignDeliveryView.as_view(), name='order_assign'),
]
