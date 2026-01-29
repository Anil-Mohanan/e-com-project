from django.shortcuts import render
from rest_framework import viewsets, permissions, parsers,filters
from .models import Product , Category, ProductVariant
from .serializers import ProductSerializer, CategroySerializer, ProductVarinatSerializer
from .permissions import IsSellerOrAdmin
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

class ProductFilter(django_filters.FilterSet):
       
       min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte') # gte= Grater that or Equal
       
       max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte') # lte = Lesser than or Equal

       brand = django_filters.CharFilter(lookup_expr='icontains')

       class Meta:
              model = Product
              fields = ['category', 'brand', 'is_active']

class ProductViewSet(viewsets.ModelViewSet):
      """A unified Viewset for viewing and editing products.
      -cutomers can read (list/retrieve)
      -admin can write (create/update/delete)"""
      


      queryset = Product.objects.all()
      serializer_class = ProductSerializer
      
      lookup_field = 'slug' # instead of looking up by ID (products/1), we look up by slug (products/nike-air-max
      
      parser_classes = [parsers.MultiPartParser, parsers.FormParser]
       #get_permissions: Instead of setting one rule for everything ,we check *what* the user is trying to do.
      filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter] 
      
      search_fields = ['name','description', 'brand', 'category__name']

      filterset_class = ProductFilter
      

      ordering_fields = ['price', 'created_at']
      ordering = ['-created_at'] # Default sort: Newest first
      
       
       
      def get_permissions(self):
             if self.request.method in permissions.SAFE_METHODS:
                     return [permissions.AllowAny()] # if they just want to READ (GET), let anyone in
             else:
                    return [IsSellerOrAdmin()] # if they want to write (POST,PUT, DELETE) chekc if they are a Seller
       
class CategoryViewSet(viewsets.ModelViewSet):
       
       """Viewset for Categories.
       Same Logic: Public can view, only Admin can edit"""

       queryset = Category.objects.all()
       serializer_class = CategroySerializer
       lookup_field = 'slug'

       def get_permissions(self):
              if self.request.method in permissions.SAFE_METHODS:
                     return [permissions.AllowAny()]
              else:
                     return [IsSellerOrAdmin()]

class ProductVariantViewSet(viewsets.ModelViewSet):
       """Manage Vairants (Size/color) for Products Admin create the Main product first , then add the varians here"""

       queryset = ProductVariant.objects.all()
       serializer_class = ProductVarinatSerializer
       permission_classes = [IsSellerOrAdmin]

       def get_queryset(self):
              """Allow filtering variants by  product.
              Example. /api/variants/?product_id = 1 -> Show only variants for Product#1"""

              product_id = self.request.query_params.get('product_id')
              if product_id:
                     return self.queryset.filter(product_id=product_id)
              return self.queryset
