from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShippingAddressViewSet, CartViewSet, CheckoutViewSet, 
    OrderHistoryViewset, AdminOrderViewSet
)

# We only use the router for standard models like addresses
router = DefaultRouter()
router.register(r'addresses', ShippingAddressViewSet, basename='addresses')

urlpatterns = [
    # Include the automated router URLs
    path('', include(router.urls)),

    # Cart ViewSet actions mapped manually
    path('cart/', CartViewSet.as_view({'get': 'list'}), name='cart-view'),
    path('add_to_cart/', CartViewSet.as_view({'post': 'add_to_cart'}), name='cart-add'),
    path('update_quantity/', CartViewSet.as_view({'post': 'update_quantity'}), name='cart-update'),
    path('remove_item/', CartViewSet.as_view({'post': 'remove_item'}), name='cart-remove'),

    # Checkout ViewSet mapped manually
    path('checkout/', CheckoutViewSet.as_view({'post': 'create'}), name='checkout'),

    # Order History mapped manually
    path('history/', OrderHistoryViewset.as_view({'get': 'list'}), name='order-history'),
    path('<uuid:order_id>/cancel_order/', OrderHistoryViewset.as_view({'post': 'cancel_order'}), name='order-cancel'),
    
    path('history/<uuid:order_id>/', OrderHistoryViewset.as_view({'get': 'retrieve'}), name='order-detail'),


    # Admin actions mapped manually
    path('admin/all/', AdminOrderViewSet.as_view({'get': 'list'}), name='admin-orders'),
    path('admin/<uuid:order_id>/mark_as_paid/', AdminOrderViewSet.as_view({'patch': 'mark_as_paid'}), name='order-mark-paid'),
    path('admin/<uuid:order_id>/update_status/', AdminOrderViewSet.as_view({'patch': 'update_status'}), name='order-update-status'),
]
