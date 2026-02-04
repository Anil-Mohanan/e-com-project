from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet,ProductVariantViewSet, ReveiwViewSet

router = DefaultRouter()
router.register(r'products',ProductViewSet)
router.register(r'categories',CategoryViewSet)
router.register(r'variants',ProductVariantViewSet)
router.register(r'reviews',ReveiwViewSet, basename='reviews')



#The router automatically generats the URL patters for us.
urlpatterns = [
    path('',include(router.urls)),
]
