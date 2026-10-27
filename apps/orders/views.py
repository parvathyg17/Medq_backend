from django.db import transaction
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import generics, views, status, permissions
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminUserRole, IsDeliveryPersonRole
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from .services import OrderPlacementService

User = get_user_model()


class OrderConfirmView(views.APIView):
    """
    POST /api/orders/confirm and POST /api/orders/
    Places an order atomically, validates inventory, and decrements stock.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            order = OrderPlacementService.create_order(
                user=request.user,
                data=request.data,
                session_key=request.session.session_key
            )
            serializer = OrderSerializer(order, context={'request': request})
            return Response({
                "success": True,
                "message": "Order placed successfully!",
                "order": serializer.data,
                "id": order.id,
                "orderNumber": order.order_number
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class OrderListView(generics.ListAPIView):
    """
    GET /api/orders/ and GET /api/orders/all
    Returns order history.
    - Admins: all orders
    - Customers: orders matching their user account or email
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and (user.role == 'ADMIN' or user.is_staff):
            return Order.objects.all().select_related('delivery_boy').prefetch_related('order_items__product').distinct()
        elif user.is_authenticated:
            from django.db.models import Q
            return Order.objects.filter(
                Q(user=user) | Q(email__iexact=user.email)
            ).select_related('delivery_boy').prefetch_related('order_items__product').distinct()
        else:
            # If email is provided as query param
            email = self.request.query_params.get('email')
            if email:
                return Order.objects.filter(email__iexact=email).select_related('delivery_boy').prefetch_related('order_items__product').distinct()
            return Order.objects.none()


class OrderDetailView(views.APIView):
    """
    GET /api/orders/<id_or_number>/
    Retrieves order by numeric ID or order_number (e.g. MEDQ-DEMO-001).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk=None, lookup=None, id=None):
        search_val = lookup or pk or id
        if not search_val:
            return Response({"error": "Order ID or order number is required."}, status=status.HTTP_400_BAD_REQUEST)

        order = None
        if str(search_val).isdigit():
            order = Order.objects.filter(pk=int(search_val)).prefetch_related('order_items__product').first()
        if not order:
            order = Order.objects.filter(order_number__iexact=str(search_val)).prefetch_related('order_items__product').first()

        if not order:
            return Response({"error": f"Order '{search_val}' could not be located in our clinical registry."}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderCancelView(views.APIView):
    """
    PUT /api/orders/cancel-order/<id>/ and DELETE /api/orders/<id>/
    Cancels an order and replenishes stock safely inside an atomic transaction.
    Cancellation is strictly prohibited once the order has been shipped or dispatched.
    """
    permission_classes = [permissions.AllowAny]

    def cancel_logic(self, order_id):
        order = get_object_or_404(Order, pk=order_id)
        if order.status == Order.Status.CANCELLED:
            return Response({"message": "Order is already cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        # Disallow cancellation if product has shipped or reached further fulfillment stages
        disallowed_statuses = [
            Order.Status.SHIPPED,
            Order.Status.OUT_FOR_DELIVERY,
            Order.Status.DELIVERED,
            Order.Status.RETURN_REQUESTED,
            Order.Status.RETURNED
        ]
        if order.status in disallowed_statuses:
            return Response({
                "message": f"Order cannot be cancelled because it is already {order.get_status_display().lower()}. Cancellation is only permitted prior to dispatch."
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Replenish stock for all items
            for item in order.order_items.all():
                if item.product:
                    item.product.stock_quantity += item.quantity
                    item.product.save(update_fields=['stock_quantity'])

            order.status = Order.Status.CANCELLED
            order.save(update_fields=['status'])

        return Response({"message": "Order cancelled successfully and reserved inventory was restored."}, status=status.HTTP_200_OK)

    def put(self, request, id=None):
        return self.cancel_logic(id)

    def delete(self, request, id=None):
        return self.cancel_logic(id)


VALID_FORWARD_TRANSITIONS = {
    Order.Status.PENDING: [Order.Status.CONFIRMED, Order.Status.CANCELLED],
    Order.Status.CONFIRMED: [Order.Status.PROCESSING, Order.Status.CANCELLED],
    Order.Status.PROCESSING: [Order.Status.SHIPPED, Order.Status.CANCELLED],
    Order.Status.SHIPPED: [Order.Status.OUT_FOR_DELIVERY],
    Order.Status.OUT_FOR_DELIVERY: [Order.Status.DELIVERED],
    Order.Status.DELIVERED: [Order.Status.RETURN_REQUESTED],  # Must be requested by customer
    Order.Status.RETURN_REQUESTED: [Order.Status.RETURNED, Order.Status.RETURN_REJECTED],  # Decided by admin
    Order.Status.RETURNED: [],
    Order.Status.RETURN_REJECTED: [],
    Order.Status.CANCELLED: [],
}


class OrderReturnView(views.APIView):
    """
    POST /api/orders/<id>/return/
    Allows customer to request equipment return for delivered orders only.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, id=None):
        order = get_object_or_404(Order, pk=id)
        if order.status != Order.Status.DELIVERED:
            return Response({
                "message": f"Return requests can only be initiated for delivered orders. Current order status is '{order.get_status_display()}'."
            }, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason') or request.query_params.get('reason', 'Customer return requested')
        from django.utils import timezone
        order.status = Order.Status.RETURN_REQUESTED
        order.return_reason = reason
        order.return_requested_at = timezone.now()
        order.save(update_fields=['status', 'return_reason', 'return_requested_at'])

        return Response({
            "message": "Equipment return request submitted successfully. Our biomedical returns team will verify the equipment condition.",
            "status": order.status
        }, status=status.HTTP_200_OK)


class AdminReturnListView(views.APIView):
    """
    GET /api/orders/returns/
    Returns all orders with return requests or return history.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        status_param = request.query_params.get('status')
        queryset = Order.objects.filter(
            status__in=[Order.Status.RETURN_REQUESTED, Order.Status.RETURNED, Order.Status.RETURN_REJECTED]
        ).select_related('delivery_boy').prefetch_related('order_items').order_by('-return_requested_at', '-updated_at')

        if status_param and status_param.upper() != 'ALL':
            queryset = queryset.filter(status=status_param.lower())

        serializer = OrderSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminApproveReturnView(views.APIView):
    """
    POST /api/orders/<id>/return/approve/
    Admin approves return request:
    - Status transitions to 'returned'.
    - Medical inventory is atomically replenished into stock.
    - Records return_processed_at and admin response.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, id=None):
        order = get_object_or_404(Order, pk=id)
        if order.status != Order.Status.RETURN_REQUESTED:
            return Response({
                "message": f"Only orders in 'Return Requested' status can be approved. Current status: '{order.get_status_display()}'."
            }, status=status.HTTP_400_BAD_REQUEST)

        admin_note = request.data.get('adminNote') or request.data.get('response') or 'Equipment inspected, sanitized, and approved by biomedical team.'

        from django.utils import timezone
        with transaction.atomic():
            for item in order.order_items.all():
                if item.product:
                    item.product.stock_quantity += item.quantity
                    item.product.save(update_fields=['stock_quantity'])

            order.status = Order.Status.RETURNED
            order.return_admin_response = admin_note
            order.return_processed_at = timezone.now()
            order.save(update_fields=['status', 'return_admin_response', 'return_processed_at'])

        return Response({
            "message": "Equipment return approved successfully. Inventory stock has been safely replenished.",
            "status": order.status
        }, status=status.HTTP_200_OK)


class AdminRejectReturnView(views.APIView):
    """
    POST /api/orders/<id>/return/reject/
    Admin rejects return request:
    - Status transitions to 'return_rejected'.
    - Inventory is NOT restocked.
    - Records admin rejection justification and return_processed_at.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, id=None):
        order = get_object_or_404(Order, pk=id)
        if order.status != Order.Status.RETURN_REQUESTED:
            return Response({
                "message": f"Only orders in 'Return Requested' status can be rejected. Current status: '{order.get_status_display()}'."
            }, status=status.HTTP_400_BAD_REQUEST)

        rejection_reason = request.data.get('rejectionReason') or request.data.get('response') or 'Return request does not meet biomedical warranty or return criteria.'

        from django.utils import timezone
        order.status = Order.Status.RETURN_REJECTED
        order.return_admin_response = rejection_reason
        order.return_processed_at = timezone.now()
        order.save(update_fields=['status', 'return_admin_response', 'return_processed_at'])

        return Response({
            "message": "Equipment return request has been rejected.",
            "status": order.status,
            "rejectionReason": rejection_reason
        }, status=status.HTTP_200_OK)


class OrderAssignDeliveryView(views.APIView):
    """
    POST /api/orders/assign and POST /api/delivery/assign
    Graceful stub for legacy compatibility (orders are managed directly by admin status).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({"message": "Delivery assignment is automated. Orders are managed directly via status updates."}, status=status.HTTP_200_OK)


class OrderRemoveDeliveryView(views.APIView):
    """
    POST /api/delivery/remove
    Graceful stub for legacy compatibility.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        return Response({"message": "Delivery assignment removed."}, status=status.HTTP_200_OK)


class OrderStatusUpdateView(views.APIView):
    """
    PUT /api/orders/<id>/status/ or PUT /api/delivery/update-status/<id>
    Admin status management: Confirmed -> Processing -> Shipped -> Out for Delivery -> Delivered.
    Strictly prevents backwards status transitions ("the status dont go back").
    """
    permission_classes = [permissions.AllowAny]

    def put(self, request, id=None):
        new_status = request.data.get('status') or request.query_params.get('status')
        if not new_status:
            return Response({"message": "Status parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, pk=id)
        normalized = new_status.strip().lower()

        if normalized == order.status:
            return Response({"message": f"Order status is already '{order.status}'."}, status=status.HTTP_200_OK)

        valid_statuses = [s.value for s in Order.Status]
        if normalized not in valid_statuses:
            return Response({"message": f"Invalid status '{new_status}'. Valid values: {valid_statuses}"}, status=status.HTTP_400_BAD_REQUEST)

        # Enforce forward-only workflow rules: The status CANNOT go backwards
        allowed_transitions = VALID_FORWARD_TRANSITIONS.get(order.status, [])
        if normalized not in allowed_transitions:
            return Response({
                "message": f"Status cannot go backwards or skip workflow stages. Order in '{order.get_status_display()}' cannot transition to '{normalized}'."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Rule: Only customers can initiate return_requested upon delivery
        if normalized == Order.Status.RETURN_REQUESTED:
            return Response({
                "message": "Return requests must be initiated by the customer upon delivery."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Handle Cancellation
        if normalized == Order.Status.CANCELLED:
            cancel_view = OrderCancelView()
            return cancel_view.cancel_logic(id)

        # Handle Return Approval
        if normalized == Order.Status.RETURNED:
            approve_view = AdminApproveReturnView()
            return approve_view.post(request, id=id)

        # Handle Return Rejection
        if normalized == Order.Status.RETURN_REJECTED:
            reject_view = AdminRejectReturnView()
            return reject_view.post(request, id=id)

        # Standard forward progress (Confirmed -> Processing -> Shipped -> Out for Delivery -> Delivered)
        order.status = normalized
        order.save(update_fields=['status'])
        return Response({
            "message": f"Order status advanced to {order.get_status_display()}.",
            "status": order.status
        }, status=status.HTTP_200_OK)


class OrderTotalCountView(views.APIView):
    """
    GET /api/orders/total
    Returns total order count for Admin dashboard.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total = Order.objects.count()
        return Response({"totalOrders": total})


class DeliveryAssignedOrdersView(generics.ListAPIView):
    """
    GET /api/delivery/assigned-orders/<deliveryBoyId>
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = OrderSerializer

    def get_queryset(self):
        delivery_boy_id = self.kwargs.get('deliveryBoyId')
        return Order.objects.filter(delivery_boy_id=delivery_boy_id).order_by('-created_at')
