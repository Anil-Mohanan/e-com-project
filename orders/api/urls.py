from django.urls import path , include
from rest_framework.routers import DefaultRouter
from .views import ShippingAddressViewSet, CartViewSet, CheckoutViewSet,OrderHistoryViewset,AdminOrderViewSet

router = DefaultRouter()
router.register(r'cart',CartViewSet,basename='cart')
router.register(r'checkout',CheckoutViewSet,basename='checkout')
router.register(r'orderhistory',OrderHistoryViewset,basename='orderhistory')
router.register(r'admin',AdminOrderViewSet,basename='admin')
router.register(r'addresses',ShippingAddressViewSet,basename='addresses')
urlpatterns = [
    path('',include(router.urls))
]
