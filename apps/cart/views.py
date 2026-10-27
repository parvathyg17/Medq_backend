from django.shortcuts import get_object_or_404
from rest_framework import views, status, permissions
from rest_framework.response import Response

from apps.products.models import Product
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer


def get_or_create_cart(request):
    """
    Retrieves the cart for the authenticated user, or creates one via session key.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


class CartDetailView(views.APIView):
    """
    GET /api/cart/
    Returns the items in the cart. Supports ?summary=true to return the full cart object.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        cart = get_or_create_cart(request)
        if request.query_params.get('summary') == 'true':
            serializer = CartSerializer(cart, context={'request': request})
            return Response(serializer.data)
        
        # Default: return list of CartItemSerializer objects for direct React compatibility
        serializer = CartItemSerializer(cart.items.all(), many=True, context={'request': request})
        return Response(serializer.data)


class CartAddView(views.APIView):
    """
    POST /api/cart/add/
    Add product to cart with stock validation.
    Accepts: { productId, quantity?: 1 }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        product_id = request.data.get('productId') or request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if not product_id:
            return Response({"error": "productId is required."}, status=status.HTTP_400_BAD_REQUEST)

        if quantity < 1:
            return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, pk=product_id)
        if not product.is_active:
            return Response({"error": "This product is no longer available."}, status=status.HTTP_400_BAD_REQUEST)

        if product.stock_quantity <= 0:
            return Response({"error": "This product is currently out of stock."}, status=status.HTTP_400_BAD_REQUEST)

        cart = get_or_create_cart(request)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        new_quantity = quantity if created else (cart_item.quantity + quantity)
        if new_quantity > 5:
            return Response({
                "error": "Maximum order limit of 5 units reached for this item."
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_quantity > product.stock_quantity:
            available = product.stock_quantity
            return Response({
                "error": f"Cannot add {new_quantity} items. Only {available} available in stock."
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = new_quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartUpdateView(views.APIView):
    """
    PUT /api/cart/update/<productId>/
    Updates item quantity, validating current stock.
    Accepts: { quantity: <number> }
    """
    permission_classes = [permissions.AllowAny]

    def put(self, request, productId=None):
        new_quantity = int(request.data.get('quantity', 1))
        if new_quantity < 1:
            return Response({"error": "Quantity must be at least 1."}, status=status.HTTP_400_BAD_REQUEST)

        if new_quantity > 5:
            return Response({
                "error": "Maximum order limit of 5 units reached for this item."
            }, status=status.HTTP_400_BAD_REQUEST)

        cart = get_or_create_cart(request)
        cart_item = get_object_or_404(CartItem, cart=cart, product_id=productId)

        if new_quantity > cart_item.product.stock_quantity:
            return Response({
                "error": f"Only {cart_item.product.stock_quantity} units available in stock."
            }, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = new_quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartRemoveView(views.APIView):
    """
    DELETE /api/cart/remove/<productId>/
    Removes item from cart.
    """
    permission_classes = [permissions.AllowAny]

    def delete(self, request, productId=None):
        cart = get_or_create_cart(request)
        deleted, _ = CartItem.objects.filter(cart=cart, product_id=productId).delete()
        if deleted:
            return Response({"message": "Item removed from cart."}, status=status.HTTP_200_OK)
        return Response({"error": "Item not found in cart."}, status=status.HTTP_404_NOT_FOUND)


class CartClearView(views.APIView):
    """
    DELETE /api/cart/clear/
    Empties the cart.
    """
    permission_classes = [permissions.AllowAny]

    def delete(self, request):
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        return Response({"message": "Cart cleared successfully."}, status=status.HTTP_200_OK)
