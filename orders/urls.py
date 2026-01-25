from django.urls import path , include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet,ShippingAddressViewSet

router = DefaultRouter()
router.register(r'orders',OrderViewSet,basename='order')
router.register(r'addresses',ShippingAddressViewSet,basename='address')
urlpatterns = [
    path('',include(router.urls))
]
