from django.urls import path
from .views import (
    CartDetailView,
    CartAddView,
    CartUpdateView,
    CartRemoveView,
    CartClearView
)

urlpatterns = [
    path('', CartDetailView.as_view(), name='cart_detail'),
    path('add', CartAddView.as_view(), name='cart_add_legacy'),
    path('add/', CartAddView.as_view(), name='cart_add'),
    path('update/<int:productId>', CartUpdateView.as_view(), name='cart_update_legacy'),
    path('update/<int:productId>/', CartUpdateView.as_view(), name='cart_update'),
    path('remove/<int:productId>', CartRemoveView.as_view(), name='cart_remove_legacy'),
    path('remove/<int:productId>/', CartRemoveView.as_view(), name='cart_remove'),
    path('clear/', CartClearView.as_view(), name='cart_clear'),
]
