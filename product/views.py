from django.shortcuts import render
from rest_framework import viewsets, permissions, parsers,filters,status
from rest_framework.response import Response
from .models import Product , Category, ProductVariant, Review
from .serializers import ProductSerializer, CategorySerializer, ProductVariantSerializer, ReviewSerializer
from .permissions import IsSellerOrAdmin, IsReviewAuthorOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from orders.models import Order, OrderItem 
from rest_framework.decorators import action
from django.db.models import Avg, Count
from django.core.cache import cache
from config.utils import error_response, success_response
from config.cache_utils import cache_response
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .services import add_review_process, build_comparison_matrix
import logging


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
      
       queryset = Product.objects.select_related('category').prefetch_related('variants','images').annotate(average_rating = Avg('reviews__rating'),review_count = Count('reviews'))

       serializer_class = ProductSerializer
      
       lookup_field = 'slug' # instead of looking up by ID (products/1), we look up by slug (products/nike-air-max
      
       parser_classes = [parsers.MultiPartParser, parsers.FormParser,parsers.JSONParser]
       #get_permissions: Instead of setting one rule for everything ,we check *what* the user is trying to do.
       filter_backends = [DjangoFilterBackend,filters.OrderingFilter] 
      

       filterset_class = ProductFilter
      

       ordering_fields = ['price', 'created_at']
       ordering = ['-created_at'] # Default sort: Newest first
       def get_queryset(self):
              search_term = self.request.query_params.get('search')

              queryset = Product.objects.select_related('category').prefetch_related('variants','images').annotate(average_rating = Avg ('reviews__rating'),review_count = Count('reviews'))
              #intercepting the query to apply PostgreSQL Full-Text Search because standard SQL LIKE queries are too slow and lack relevance ranking for e-commerce.
              if search_term: 
                     # this creates a tsvector. Write a note that Postgres will automatically tokenize the text, remove stop words, and reduce words to their lexemes (root words). Also, explain the weighting: A (highest priority) for name, down to C (lowest) for description.
                     vector = SearchVector('name', weight='A') + \
                              SearchVector('brand', weight='B') + \
                              SearchVector('description', weight='C') + \
                              SearchVector('category__name', weight='C')

                     # this converts the user's raw input string into a tsquery, applying the exact same tokenization and lexing rules as the vector so they can be mathematically compared.
                     query = SearchQuery(search_term)
                     #SearchRank compares the tsvector and tsquery. State that it calculates a density score based on matches and weightings, creating a temporary rank column in the database response
                     queryset = queryset.annotate(rank = SearchRank(vector,query))
                     #filter out ranks below 0.001 to remove completely irrelevant results, and then sort descending by rank (-rank) so the most relevant products appear first.
                     queryset = queryset.filter(rank__gte = 0.001).order_by('-rank')
              
              return queryset

       def get_permissions(self):
       
             if self.request.method in permissions.SAFE_METHODS:
                     return [permissions.AllowAny()] # if they just want to READ (GET), let anyone in
             else:
                    return [IsSellerOrAdmin()] # if they want to write (POST,PUT, DELETE) chekc if they are a Seller
       @action(detail=True, methods=['post'],permission_classes = [permissions.IsAuthenticated])  # set detail True for to foucse on one speicifc item . write permission_classes inside action to over ride the defualt IsAuthenticated . Reviwes return by Customers not Sellers
       def add_review(self,request,slug=None):
              product = self.get_object() # get the product based on the slug in URL
              user = request.user
              data = request.data
             
              #check if the user already reviewd
              if product.reviews.filter(user=user).exists():
                     return error_response(message="You have already reviewd this Product", status_code=400)
       
                     # 2 verfication : did the buy it?
                     # checking if and orders exist in that is delvered (or any stauts for now)
                     had_bought = OrderItem.objects.filter(
                           order__user = user,
                           product = product
                     ).exists()
                     if not had_bought:
                           return Response(
                                  messages =  'You can only reiview products you have purchased.',
                                  status_code = 400
                           )
              review = add_review_process(
                     product = product,
                     user = user,
                     rating= data.get('rating',0),
                     comment = data.get('comment','')
              )
              if review:                  
                     return success_response(message="Review added Successfully", status_code=201)

             
       @cache_response(key_prefix="product_list",error_message="Unable to Load Products")
       def list(self,request,*args, **kwargs):
              response = super().list(request,*args, **kwargs)
              return response

       @cache_response(key_prefix="product_detail",error_message="Product not Found")      
       def retrieve(self, request, *args, **kwargs):
              instance = self.get_object()
              serializer = self.get_serializer(instance)
              data = serializer.data
              return Response(data) 
       
       
       @action(detail=False,methods=['get'],permission_classes=[permissions.AllowAny])
       def compare(self,request):
              products_ids_string = request.query_params.get('ids')

              if not products_ids_string:
                     return error_response(message = 'Please provide product IDs to compare using ?ids =...',status_code = 400)

              try:
                     comparsion_matrix = build_comparison_matrix(products_ids_string)
                     
                     return success_response(message ="Comparsion Successfull",status_code = 200,data=comparsion_matrix)
              except ValueError as e:
                     return error_response(message = str(e),status_code= 400)


class CategoryViewSet(viewsets.ModelViewSet):
       
       """Viewset for Categories.
       Same Logic: Public can view, only Admin can edit"""

       queryset = Category.objects.all()
       serializer_class = CategorySerializer
       lookup_field = 'slug'

       def get_permissions(self):
              if self.request.method in permissions.SAFE_METHODS:
                     return [permissions.AllowAny()]
              else:
                     return [permissions.IsAdminUser()]

       @cache_response(key_prefix="category_list",error_message="Unable to Fetch Categories at this time")
       def list(self,request,*args, **kwargs):
              response = super().list(request,*args, **kwargs)
              return response

       @cache_response(key_prefix="category_detail",error_message="Category not Found")
       def retrieve(self, request, *args, **kwargs):
              instance = self.get_object() # This is the "Search" step. It uses the slug and the queryset you defined at the top of the class to find the exact row in your database. 
              serializer = self.get_serializer(instance) # what is this line is for 
              data = serializer.data # what is this for 
              return Response(data)

class ProductVariantViewSet(viewsets.ModelViewSet):
       """Manage Vairants (Size/color) for Products Admin create the Main product first , then add the varians here"""

       queryset = ProductVariant.objects.all()
       serializer_class = ProductVariantSerializer
       permission_classes = [IsSellerOrAdmin]
       lookup_field = 'slug'

       def get_queryset(self):
              """Allow filtering variants by  product.
              Example. /api/variants/?product_id = 1 -> Show only variants for Product#1"""

              product_id = self.request.query_params.get('product')
              if product_id:
                     return self.queryset.filter(product_id=product_id)
              return self.queryset


       @cache_response(key_prefix="product_variant_list",error_message="Unable to fetch Product Variant")
       def list(self, request,*args, **kwargs):
              response = super().list(request,*args, **kwargs)
              return response

       @cache_response(key_prefix="product_variant_detail", error_message="This Variant is not Avalible")
       def retrieve(self, request, *args, **kwargs):
              instance = self.get_object()
              serializer = self.get_serializer(instance)
              data = serializer.data
              return Response(data)
       
class ReviewViewSet(viewsets.ModelViewSet):
       """Handles:
       -get (list/retrive)
       put/delete (update- restricted to author)
       delete(restricted to author/admin)"""

       queryset = Review.objects.all()
       serializer_class = ReviewSerializer
       permission_classes = [IsReviewAuthorOrReadOnly] # the Custom permission

       
       def get_queryset(self):
              # if the user ask for specific_reviewadd_review
              if self.action in ['retrieve', 'update', 'partial_update', 'destroy','list'] or self.request.user.is_staff:
                     queryset = Review.objects.all().order_by('-created_at') # at this stage it contian reviews or every product every sold
                     product_id = self.request.query_params.get('product_id')# getting the review of a specific product
                     if product_id:
                            queryset = queryset.filter(product_id=product_id)#filtered or review of the specific product 
                     return queryset
              return Review.objects.none()
       
       http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options'] # only allow methods form this list . that means disabling the POST and the GET  list method not retrive 
       @cache_response(key_prefix="review_list",error_message="Unable to show the Review")
       def list(self,request,*args, **kwargs):
                
              response = super().list(request,*args, **kwargs)
             
              return response

       @cache_response(key_prefix="review_detail",error_message="Review Not Found")
       def retrieve(self, request, *args, **kwargs):
              
              instance = self.get_object()
              serializer = self.get_serializer(instance)
              data = serializer.data
              
              return Response(data)
