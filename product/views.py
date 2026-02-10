from django.shortcuts import render
from rest_framework import viewsets, permissions, parsers,filters,status
from rest_framework.response import Response
from .models import Product , Category, ProductVariant, Review
from .serializers import ProductSerializer, CategroySerializer, ProductVarinatSerializer, ReviewSerializer
from .permissions import IsSellerOrAdmin, IsReviewAuthorOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from orders.models import Order, OrderItem 
from rest_framework.decorators import action
from django.db.models import Avg, Count
from django.core.cache import cache
from config.utils import error_response
import logging

class ProductFilter(django_filters.FilterSet):
       
       min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte') # gte= Grater that or Equal
       
       max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte') # lte = Lesser than or Equal

       brand = django_filters.CharFilter(lookup_expr='icontains')

       class Meta:
              model = Product
              fields = ['category', 'brand', 'is_active']
logger = logging.getLogger(__name__)
class ProductViewSet(viewsets.ModelViewSet):
      """A unified Viewset for viewing and editing products.
      -cutomers can read (list/retrieve)
      -admin can write (create/update/delete)"""
      
      queryset = Product.objects.select_related('category').prefetch_related('variants','images').annotate(average_rating = Avg('reviews__rating'),review_count = Count('reviews'))
      serializer_class = ProductSerializer
      
      lookup_field = 'slug' # instead of looking up by ID (products/1), we look up by slug (products/nike-air-max
      
      parser_classes = [parsers.MultiPartParser, parsers.FormParser,parsers.JSONParser]
       #get_permissions: Instead of setting one rule for everything ,we check *what* the user is trying to do.
      filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter] 
      
      search_fields = ['name','description', 'brand', 'category__name']

      filterset_class = ProductFilter
      

      ordering_fields = ['price', 'created_at']
      ordering = ['-created_at'] # Default sort: Newest first
 
      def get_permissions(self):
             if self.action == 'add_reveiw':
                    return [permissions.IsAuthenticated]
             
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
                    return Response(
                           {'error': 'You have already reviewd this product'},
                           status= status.HTTP_400_BAD_REQUEST
                    )
                    # 2 verfication : did the buy it?
                    # checking if and orders exist in that is delvered (or any stauts for now)
                    had_bought = OrderItem.objects.filter(
                           order__user = user,
                           product = product
                    ).exists()
                    if not had_bought:
                           return Response(
                                  {'error': 'You can only reiview products you have purchased.'},
                                  status=status.HTTP_403_FORBIDDEN
                           )
             Review.objects.create(
                     product = product,
                     user = user,
                     rating= data.get('rating',0),
                     comment = data.get('comment','')
              )                    
             return Response({'Message': 'Reivew added Succesfully'}, status=status.HTTP_201_CREATED)
      
      def list(self,request,*args, **kwargs):
              cache_key = f"product_list{request.query_params.urlencode()}"
              try: # Read Attempt
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                    logger.error(f"Cache Read Error on Product list: {e}")
                           # log the error to debug.log insted of printing
              try: #Data base Fetch
                     response = super().list(request,*args, **kwargs)
              except Exception as e:
                     return error_response(message="Service temproraily Unavailabe",log_message=f"Data Base Error on Product list {e}")
              try: # Wrtie Attempt
                     cache.set(cache_key,response.data,900)
              except Exception as e:
                    logger.error(f"Cache Write Error on Product list: {e}")
              return response
      def retrieve(self, request, *args, **kwargs):
             slug = kwargs.get('slug')
             cache_key = f"product_detail_{slug}"
             try:
                   stored_data = cache.get(cache_key) 
                   if stored_data:
                          return Response(stored_data)
             except Exception as e:
                    logger.error(f"Error fetching cache:{e}")
             try:
                     instance = self.get_object()
                     serializer = self.get_serializer(instance)
                     data = serializer.data
             except Exception as e:
                     return error_response(message="Prodct Not Found or Service unavilable",status_code= 404, log_message=f"Error in Fetching data from DB: {e}")
             try:
                    cache.set(cache_key,data,900)
             except Exception as e:
                    logger.error(F"Cache Write error {e}") 
             return Response(data) 
       

              
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
       def list(self,request,*args, **kwargs):
              cache_key = "category_list_all"
              try:
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"Cache error on Category list: {e}")
              try:       
                     response = super().list(request,*args, **kwargs)
              except Exception as e:
                     return error_response(
                            message="Unable to fetch categories at this time.", log_message=f"Databse Error on Category Viewset: {e}")
              try:
                     cache.set(cache_key,response.data,900)
              except  Exception as e:
                     logger.error(f"Cache Write Error on Category list: {e}")
              return response
       
       def retrieve(self, request, *args, **kwargs):
              slug = kwargs.get('slug') 
              cache_key = f"category_detail_{slug}" # how we are getting the slug in here 
              
              try: # Read Attempt
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"Error Fetching in Category Cache : {e}")
              
              try: # Data base fetch
                     instance = self.get_object() # This is the "Search" step. It uses the slug and the queryset you defined at the top of the class to find the exact row in your database. 
                     serializer = self.get_serializer(instance) # what is this line is for 
                     data = serializer.data # what is this for 
              except Exception as e:
                     return error_response(
                     message = "Category not found or  removed",
                     status_code = 404,
                     log_message = f"DB error in Category Viewset : {e}")
              try:
                     cache.set(cache_key,data,900)
              except Exception as e:

                     logger.error(f"Cache Write Error on Category: {e}")
              return Response(data)


class ProductVariantViewSet(viewsets.ModelViewSet):
       """Manage Vairants (Size/color) for Products Admin create the Main product first , then add the varians here"""

       queryset = ProductVariant.objects.all()
       serializer_class = ProductVarinatSerializer
       permission_classes = [IsSellerOrAdmin]
       lookup_field = 'slug'

       def get_queryset(self):
              """Allow filtering variants by  product.
              Example. /api/variants/?product_id = 1 -> Show only variants for Product#1"""

              product_id = self.request.query_params.get('product_id')
              if product_id:
                     return self.queryset.filter(product_id=product_id)
              return self.queryset
       def list(self, request,*args, **kwargs):
              stored_data = None
              product_id = None
              product_id = request.query_params.get('product_id')
              params = request.query_params.urlencode()
              cache_key = f"product_variants_{params}"
              response = None
              try:
                     if product_id:
                            stored_data = cache.get(cache_key)
                            if stored_data:
                                   return Response(stored_data)
              except Exception as e:
                     logger.error(f"Cache Read Error on Product Variant list:{e}")
              try:
                     response = super().list(request,*args, **kwargs)
              except Exception as e:
                     logger.error(f"Database Errro on Product Variant list:{e}")
                     return error_response(message="Unable to fetch Product Variant list",log_message=f"Data base Error on Product Varinat Viewset: {e}")
              try:
                     if product_id and response:
                            cache.set(cache_key,response.data,900)
              except Exception as e:
                     logger.error(f"Cache Write Error on Product Variant List")
                     
              return response

       def retrieve(self, request, *args, **kwargs):
              slug = kwargs.get('slug')
              cache_key = f"Product_varint_{slug}"
              try:
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"Error in ProductVariant Viewset Caching :{e}")
              try:
                     instance = self.get_object()
                     serializer = self.get_serializer(instance)
                     data = serializer.data
              except Exception as e:
                     return error_response(
                            message="This Variant is not Avalible",
                            status_code=404,
                            log_message=f"Error in DB Fetching in Product Variant Viewset: {e}"
                     )
              try:
                     cache.set(cache_key,data,900)
              except Exception as e:
                     logger.error(f"Error in Cahcing on Product Variant Viewset: {e}")
       
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
              # if the use ask for specific reveiw
              if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:# 
                     return Review.objects.all().order_by('-created_at')
              #if the user ask for all the review . check is the admin or not 
              if self.request.user.is_staff:
                     return Review.objects.all().order_by('-created_at')
              return Review.objects.none()
       
       http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options'] # only allow methods form this list . that means disabling the POST and the GET  list method not retrive 
       
       def list(self,request,*args, **kwargs):
              product_id = request.query_params.get('product_id')
              if product_id:
                     params = request.query_params.urlencode()
                     cache_key = f"reviews_product_{params}"
              else:
                     cache_key = "review_list_all"
              try:       
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"Cache Read Error on Product Reveiw list : {e}")
              try:       
                     response = super().list(request,*args, **kwargs)
              except Exception as e:
                     logger.error(f'Data base Error on Review list {e}')
                     return error_response(message="unable to fetch Review list",log_message=f"Data base error on Review View Set: {e}")
              try:
                     cache.set(cache_key,response.data,900)
              except Exception as e:
                     logger.error(f"Cache Write Error on Review list : {e}")
              return response
       def retrieve(self, request, *args, **kwargs):
              pk = kwargs.get('pk')
              cache_key = f"Review_details_{pk}"
              try:
                     stored_data = cache.get(cache_key)
                     if stored_data:
                            return Response(stored_data)
              except Exception as e:
                     logger.error(f"Cache Read Error on Review: {e}")
              try:
                     instance = self.get_object()
                     serialzier = self.get_serializer(instance)
                     data = serialzier.data
              except Exception as e:
                     return error_response(
                            message="Review Not Found",
                            status_code=404,
                            log_message=f"Error in DB on ReviewViewst {e}"       
                     )
              try:
                     cache.set(cache_key,data,900)
              except Exception as e:
                     logger.error(f"error in Cache set on ReviewVieset: {e}")

              return Response(data)

                     
