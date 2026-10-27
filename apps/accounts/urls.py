from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    CurrentUserView,
    ForgotPasswordView,
    ResetPasswordView,
    ChangePasswordView,
    AddressListCreateView,
    AddressDetailView,
    AddressSetDefaultView,
    AdminUserListView,
    AdminUserDeleteView,
    DeliveryPersonnelListView,
    DeliveryPersonnelCountView,
)

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('signup/', RegisterView.as_view(), name='auth_signup'),  # Legacy compatibility
    path('login/', LoginView.as_view(), name='auth_login'),
    path('me/', CurrentUserView.as_view(), name='auth_me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='auth_forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='auth_reset_password'),

    # Addresses
    path('addresses/', AddressListCreateView.as_view(), name='address_list_create'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address_detail'),
    path('addresses/<int:pk>/set-default/', AddressSetDefaultView.as_view(), name='address_set_default'),

    # User management
    path('all/', AdminUserListView.as_view(), name='auth_users_all'),
    path('delete/<int:id>/', AdminUserDeleteView.as_view(), name='auth_user_delete'),
]
