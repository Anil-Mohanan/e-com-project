from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet,ProductVariantViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'products',ProductViewSet,basename='products')
router.register(r'categories',CategoryViewSet,basename='category')
router.register(r'variants',ProductVariantViewSet,basename='variants')
router.register(r'reviews',ReviewViewSet, basename='reviews')



#The router automatically generats the URL patters for us.
urlpatterns = [
    path('',include(router.urls)),
]