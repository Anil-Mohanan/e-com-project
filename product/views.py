from django.shortcuts import render
from rest_framework import viewsets, permissions, parsers
from .models import Product , Category, ProductVariant
from .serializers import ProductSerializer, CategroySerializer, ProductVarinatSerializer
from .permissions import IsSellerOrAdmin

class ProductViewSet(viewsets.ModelViewSet):
      """A unified Viewset for viewing and editing products.
      -cutomers can read (list/retrieve)
      -admin can write (create/update/delete)"""

      queryset = Product.objects.all()
      serializer_class = ProductSerializer
      
      lookup_field = 'slug' # instead of looking up by ID (products/1), we look up by slug (products/nike-air-max
      
      parser_classes = [parsers.MultiPartParser, parsers.FormParser]
       #get_permissions: Instead of setting one rule for everything ,we check *what* the user is trying to do.
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
              