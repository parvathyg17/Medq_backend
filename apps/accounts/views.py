import uuid
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, Address
from .permissions import IsAdminUserRole, IsDeliveryPersonRole
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    AddressSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Registers a new user (Customer or Delivery Person).
    Accepts: { name, email, phone, password, role? }
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User registered successfully!",
            "user": UserProfileSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    """
    Custom login view accepting { identifier (email or phone), password }.
    Returns JWT access & refresh tokens, user role, and profile info.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    """
    Returns and updates the profile of the currently authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class ForgotPasswordView(views.APIView):
    """
    Initiates password reset by generating a reset token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email__iexact=email)

        token = str(uuid.uuid4())
        user.reset_token = token
        user.save(update_fields=['reset_token'])

        return Response({
            "message": "Password reset token generated successfully.",
            "token": token  # Returned for testing/local convenience
        }, status=status.HTTP_200_OK)


class ResetPasswordView(views.APIView):
    """
    Sets a new password using the supplied reset token.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        user = User.objects.filter(reset_token=token).first()
        if not user:
            return Response({"message": "Invalid or expired reset token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.reset_token = None
        user.save()

        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)


class ChangePasswordView(views.APIView):
    """
    POST /api/auth/change-password/
    Updates password for currently authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']

        if not user.check_password(current_password):
            return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)


class AddressListCreateView(generics.ListCreateAPIView):
    """
    List customer addresses or create a new delivery address.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by('-is_default', '-created_at')

    def perform_create(self, serializer):
        # If user has no existing addresses, make the first one default
        is_first = not Address.objects.filter(user=self.request.user).exists()
        serializer.save(user=self.request.user, is_default=is_first or serializer.validated_data.get('is_default', False))


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AddressSerializer

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressSetDefaultView(views.APIView):
    """
    POST /api/auth/addresses/<id>/set-default/
    Promotes the specified address to default and demotes all others.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        Address.objects.filter(user=request.user).exclude(pk=address.pk).update(is_default=False)
        address.is_default = True
        address.save(update_fields=['is_default'])
        serializer = AddressSerializer(address)
        return Response({
            "message": f"'{address.full_name}' set as your primary default delivery location.",
            "address": serializer.data
        }, status=status.HTTP_200_OK)


# ==========================================
# Admin and Delivery Management Endpoints
# ==========================================

class AdminUserListView(generics.ListAPIView):
    """
    List all users (with optional filtering by role).
    """
    permission_classes = [IsAdminUserRole]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset


class AdminUserDeleteView(generics.DestroyAPIView):
    """
    Admin deletion of a user account.
    """
    permission_classes = [IsAdminUserRole]
    queryset = User.objects.all()
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response({"message": "You cannot delete your own admin account."}, status=status.HTTP_400_BAD_REQUEST)
        user.delete()
        return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)


class DeliveryPersonnelListView(generics.ListAPIView):
    """
    Returns delivery personnel (active or all).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserProfileSerializer

    def get_queryset(self):
        queryset = User.objects.filter(role=User.Role.DELIVERY_PERSON)
        available_only = self.request.query_params.get('available')
        if available_only == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset


class DeliveryPersonnelCountView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        count = User.objects.filter(role=User.Role.DELIVERY_PERSON).count()
        return Response(count)
