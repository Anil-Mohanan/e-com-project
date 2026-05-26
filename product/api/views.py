from math import exp
from django.db import IntegrityError
from rest_framework import viewsets, permissions, parsers,filters,status
from rest_framework.response import Response
from product.models import Product , Category, ProductVariant, Review 
from .serializers import ProductSerializer, CategorySerializer, ProductVariantSerializer, ReviewSerializer, ProductSearchSerializer
from .permissions import IsSellerOrAdmin, IsReviewAuthorOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework.decorators import action
from django.db.models import Avg, Count
from config.utils import error_response, success_response
from config.cache_utils import cache_response
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from product.services import (
    add_review_process,
    build_comparison_matrix,
    fast_search_catalog,
    get_trending_products_service,
    get_related_products_service,
    update_reveiw_process,
)
import logging


class ProductFilter(django_filters.FilterSet):
       
       min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte') # gte= Grater that or Equal
       
       max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte') # lte = Lesser than or Equal

       brand = django_filters.CharFilter(lookup_expr='icontains')
       
       in_stock = django_filters.BooleanFilter(field_name='stock', method='filter_in_stock')

       min_rating = django_filters.NumberFilter(field_name='average_rating',lookup_expr='gte')
       
       
       #Tell Django to fitler the 'category' query paramter
       category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
       
       def filter_in_stock(self,queryset,name,value):
              if value:
                     return queryset.filter(stock__gt = 0)
              return queryset


       class Meta:
              model = Product
              fields = [ 'brand', 'is_active','in_stock','min_rating']

class ProductViewSet(viewsets.ModelViewSet):
       """A unified Viewset for viewing and editing products.
       -cutomers can read (list/retrieve)
       -admin can write (create/update/delete)"""
      
       queryset = Product.objects.select_related('category').prefetch_related('images','images__color','variants').annotate(average_rating = Avg('reviews__rating'),review_count = Count('reviews'))

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

              queryset = Product.objects.select_related('category').prefetch_related('variants','images','images__color').annotate(average_rating = Avg ('reviews__rating'),review_count = Count('reviews'))
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

              for key, value in self.request.query_params.items():
                     #check if the query paramter starts with defined "spec_" prefix and has a value
                     if key.startswith('spec_') and value:
                            #Extract the actual specifcation key name by removing the prefix
                            spec_key = key[5:]
                            from django.db.models import Q
                            queryset = queryset.filter(Q(**{f"specifications__{spec_key}": value}) | Q(variants__attribute_name=spec_key, variants__attribute_value=value, variants__is_active=True)).distinct()
              return queryset


       def get_permissions(self):

              # 1. Explicitly allow normal Authenticated customers to leave reviews
              if self.action == 'add_review':
                     return [permissions.IsAuthenticated()]

              if self.request.method in permissions.SAFE_METHODS:
                     return [permissions.AllowAny()] # if they just want to READ (GET), let anyone in
              else:
                    return [IsSellerOrAdmin()] # if they want to write (POST,PUT, DELETE) chekc if they are a Seller
              
              
       @action(detail=True, methods=['post'],permission_classes = [permissions.IsAuthenticated])  # set detail True for to foucse on one speicifc item . write permission_classes inside action to over ride the defualt IsAuthenticated . Reviwes return by Customers not Sellers
       def add_review(self,request,*args,**kwargs):
              product = self.get_object() # get the product based on the slug in URL
              user = request.user
              data = request.data
             
              # 1. Verification: Already reviewed?
              try:
                     review = add_review_process(
                            product_id = product.id,
                            user_id = user.id,
                            rating= data.get('rating',0),
                            comment = data.get('comment','')
                     )
                     if review:                  
                            return success_response(message="Review added Successfully", status_code=201)
              except ValueError as e:
                     return error_response(message = str(e),status_code = 400)

       @action(detail=False,methods=['get'],permission_classes = [permissions.AllowAny])
       def top_rated(self,request,*args, **kwargs):
              category_slug = request.query_params.get('category')
              brand = request.query_params.get('brand')
              limit = int(request.query_params.get('limit', 5))
              
              #gatting the base queryset which is already inclucde average_rating and review_count
              queryset = self.get_queryset()
              
              #Filter out products that have zero reviews to only show rated products
              queryset = queryset.filter(review_count__gt = 0)
              
              if category_slug:
                     #if the frontend sends with category paramerter filter the queryset by catgory slug
                     queryset = queryset.filter(category__slug__iexact = category_slug)
              if brand:
                     queryset = queryset.filter(brand__iexact = brand)

              queryset = queryset.order_by('-average_rating','-review_count')[:limit]
              serializer = self.get_serializer(queryset,many = True)
              
              return success_response(message="Top reated products", status_code=200, data=serializer.data)
             
       @cache_response(key_prefix="product_list",error_message="Unable to Load Products",allowed_params=['category', 'brand', 'ordering', 'page', 'min_price', 'max_price', 'in_stock', 'min_rating', 'search'])
       def list(self,request,*args, **kwargs):
              response = super().list(request,*args, **kwargs)
              return response

       @cache_response(key_prefix="product_detail",error_message="Product not Found",allowed_params=[])      
       def retrieve(self, request, *args, **kwargs):
              try:
                     instance = self.get_object()
              except Exception:
                     return error_response(message = "Product not found", status_code = 404)
              #pass tracking context to the service so it can fire the ProductViewed event.
              # get_the_product_details now handle the event publishing internally
              from product.services import get_product_details
              get_product_details(
                     product_id=instance.id,
                     user_id = request.user.id if request.user.is_authenticated else None,
                     session_key = request.session.session_key,
              )
              serializer = self.get_serializer(instance)
              data = serializer.data
              return Response(data) 
       
       @cache_response(key_prefix="product_compare", allowed_params=['ids'])
       @action(detail=False,methods=['get'],permission_classes=[permissions.AllowAny])
       def compare(self,request,**kwargs):
              products_ids_string = request.query_params.get('ids')

              if not products_ids_string:
                     return error_response(message = 'Please provide product IDs to compare using ?ids =...',status_code = 400)

              try:
                     comparsion_matrix = build_comparison_matrix(products_ids_string)
                     
                     return success_response(message ="Comparsion Successfull",status_code = 200,data=comparsion_matrix)
              except ValueError as e:
                     return error_response(message = str(e),status_code= 400)

       @action(detail = False, methods =['get'],permission_classes = [permissions.AllowAny])
       def instant_search(self,request,*args,**kwargs):
              search_term = request.query_params.get('q','')
              results = fast_search_catalog(search_term,
              user_id = request.user.id if request.user.is_authenticated else None,
              session_key = request.session.session_key,

              )
              #seralize the redis result to add absolute URL
              serializer = ProductSearchSerializer(results, many = True, context = {'request': request})
              return success_response(message='Search complete', status_code=200,data=serializer.data)

       @action(detail=False, methods=['get'],permission_classes=[permissions.AllowAny])
       def trending(self,request, *args, **kwargs):
              """
              GET /api/products/trending/?days = 7&limit=10 Reutrns the most-viewed products
              in the last N days.
              Anyone can see this - it's public catalog data.
       
              """
              days = int(request.query_params.get('days',7))
              limit = int(request.query_params.get('limit',10))

              products = get_trending_products_service(days = days, limit = limit)

              serializer = self.get_serializer(products, many = True)

              return success_response(message = "Trending products", status_code=200, data = serializer.data)
       
       @action(detail = True, methods=['get'],permission_classes=[permissions.AllowAny])
       def related(self, request, *args, **kwargs):
              
              """
              GET /api/products/{slug}/related/
              Returns products frequently viewed in the same session as this product.
              This is the "Customers also viewed..." recommendation.
              detail=True because we operate on one specific product.
              """
              product = self.get_object()
              days = int(request.query_params.get('days', 30))
              limit = int(request.query_params.get('limit', 5))
              products = get_related_products_service(product_id = product.id, days=days, limit = limit)
              serializer = self.get_serializer(products, many = True)
              return success_response(message="Related products", status_code=200, data=serializer.data)

       def perform_update(self, serializer):
              """
              Intercepts product updates (PUT/PATCH) before they hit the database.
              We capture the old values, save the new values, and if price or stock
              changed, we log it to the AdminActionLog.
              """
              # 1. Capture old values BEFORE saving
              old_price = serializer.instance.price
              old_stock = serializer.instance.stock
              
              # 2. Save the changes to the database
              new_instance = serializer.save()
              
              # 3. Check for price changes
              if old_price != new_instance.price:
                  from analytics.services import record_admin_action
                  record_admin_action(
                      actor_id=self.request.user.id,
                      actor_email=self.request.user.email,
                      action='product.price_changed',
                      target_id=new_instance.slug,
                      old_value={'price': str(old_price)},   # str() because Decimal is not JSON serializable
                      new_value={'price': str(new_instance.price)}
                  )
                  
              # 4. Check for stock changes
              if old_stock != new_instance.stock:
                  from analytics.services import record_admin_action
                  record_admin_action(
                      actor_id=self.request.user.id,
                      actor_email=self.request.user.email,
                      action='product.stock_adjusted',
                      target_id=new_instance.slug,
                      old_value={'stock': old_stock},
                      new_value={'stock': new_instance.stock}
                  )
       @action(detail=False, methods = ['get'],permission_classes=[permissions.AllowAny])
       def brands(self,request,*args,**kwargs):
              """Returns distinc brand names from the db , optionally fitlerd by category"""
              # Read the optional category slug from the params eg : ?category = gpu
              category_slug = request.query_params.get('category')
              # start with all active products in the db
              queryset = Product.objects.filter(is_active = True)
              # narrow down to only the category
              if category_slug:
                     queryset = queryset.filter(category__slug__iexact = category_slug)
                     #extract only the unique brand names
              brand_list = (
                     queryset.exclude(brand__isnull =True)
                     .exclude(brand__exact = '')
                     .values_list('brand',flat = True)
                     .distinct()
                     .order_by('brand')
              )

              return success_response(message="Brands fetched successfully",status_code=200,data=list(brand_list))

       @action(detail= False,methods = ['get'],permission_classes = [permissions.AllowAny])
       #define the spec_options endpoint handler function
       def spec_options(self,request,*args,**kwargs):
              #Retrieve the category slug query parameter from the incoming request URL
              category_slug = request.query_params.get('category')
              if not category_slug:
                     #return successful response containing an empty dictionary of specifcation options
                     return success_response(message="No categroy spccified", status_code = 200, data = {})
              try:
                     #fetch the single category record by slug (case insensitve)
                     category = Category.objects.get(slug__iexact=category_slug)

              except Category.DoesNotExist:
                     return error_response(message="Category not found",status_code=404)
              
              #Extracting the list for required specification keys for defined on the category model(defualting to an empty list )
              keys = category.required_specs_keys or []
              # Initialzing an empty dictonary to hold the mapping of specificaton keys to distinct available values

              def natural_sort_key(val_str):#Define local natural sorting helper function for numeric & unit values
                     import re # regex

                     s = str(val_str).strip().lower() # Clean white space and convert to lowercase for uniform Comparsion
                     match = re.match(r'^([\d.]+)\s*([a-zA-Z\s]+)$', s) # Match stander float/int digits followed by any unit characters

                     if match:
                            try:
                                   num = float(match.group(1))
                                   unit = match.group(2).strip()

                                   multipliers = {  # Define dictionary of multipliers to normalize capacities/speeds to standard bases
                                           'tb': 1024 * 1024,  # Terabytes to Megabytes
                                           'gb': 1024,  # Gigabytes to Megabytes
                                           'mb': 1,  # Megabytes base
                                           'kb': 1 / 1024,  # Kilobytes to Megabytes
                                           'ghz': 1000,  # Gigahertz to Megahertz
                                           'mhz': 1,  # Megahertz base
                                    }  # End of multipliers dictionary
                                   factor = 1  # Default factor if unit doesn't require scaling (e.g. W, WHr, Cores)

                                   for unit_key, mult in multipliers.items(): # loop through to fin d a match
                                          if unit_key in unit:
                                                 factor = mult
                                                 break
                                   return (0, num * factor, val_str) # Return numeric sorting tuple with normalized scale
                            except ValueError:
                                   pass
                     nums = re.findall(r'[\d.]+',s)  # General fallback: extract the first sequence of digits/decmial point found in the string
                     if nums:
                            try:
                                   first_num = float(nums[0])# Convert first matched number to float
                                   factor = 1 # Defalt factor for text numbers
                                   if 'tb' in s:
                                          factor = 1024 * 1024
                                   elif 'gb' in s:
                                          factor = 1024
                                   elif 'ghz' in s:
                                          factor = 1000
                                   return (0, first_num * factor, val_str)
                            
                            except ValueError:
                                   pass
                     return(1,0,val_str)# Return Alphabetical sorting                                   
              spec_options = {}
              #filter all active products belonging to the matched category in the db
              products = Product.objects.filter(category = category,is_active = True)
              #Interating through each requried specification key to collect distinct values
              for key in keys:
                     #Query the distinct values for this JSONField specification key from the product queryset
                     from django.db.models.fields.json import KeyTextTransform
                     product_values = (
                            # Execute values_list on the annotaions of the JSONField specifcation key
                            products.annotate(val=KeyTextTransform(key, 'specifications')).values_list('val', flat=True).distinct()  # Filter out duplicates at the database level
                     )
                     
                     variant_values = (
                            ProductVariant.objects.filter(
                                   product__category = category,
                                   product__is_active = True,
                                   is_active = True,
                                   attribute_name = key
                            ).values_list('attribute_value',flat=True).distinct()
                     )
                     combined_values = set(product_values) | set(variant_values)
                     #fitler out None and empty strings, cast to a set of unique clean string vlaues, sort alphabetically
                     cleaned_values = sorted(list({str(v).strip() for v in combined_values if v is not None and str(v).strip() != ""}),key=natural_sort_key)
                     #Store the list of cleaned sorted values mapped to the specification key
                     spec_options[key] = cleaned_values
                     #Return a success Response containing the generated specification options map
              
              return success_response(message="Specification options fetched successfully",status_code=200,data = spec_options)

              

class CategoryViewSet(viewsets.ModelViewSet):
       
       """Viewset for Categories.
       Same Logic: Public can view, only Admin can edit"""

       queryset = Category.objects.all().prefetch_related('products', 'products__images')
       serializer_class = CategorySerializer
       lookup_field = 'slug'

       def get_permissions(self):
              if self.request.method in permissions.SAFE_METHODS:
                     return [permissions.AllowAny()]
              else:
                     return [permissions.IsAdminUser()]

       @cache_response(key_prefix="category_list",error_message="Unable to Fetch Categories at this time",allowed_params=[])
       def list(self,request,*args, **kwargs):
              response = super().list(request,*args, **kwargs)
              return response

       @cache_response(key_prefix="category_detail",error_message="Category not Found",allowed_params= [])
       def retrieve(self, request, *args, **kwargs):
              instance = self.get_object() # This is the "Search" step. It uses the slug and the queryset you defined at the top of the class to find the exact row in your database. 
              serializer = self.get_serializer(instance)  
              data = serializer.data
              return Response(data)

class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
       """Manage Vairants (Size/color) for Products Admin create the Main product first , then add the varians here"""

       queryset = ProductVariant.objects.all().order_by('id')
       serializer_class = ProductVariantSerializer
       # lookup_field = 'slug'

       def get_queryset(self):
              """Allow filtering variants by  product.
              Example. /api/variants/?product_id = 1 -> Show only variants for Product#1"""

              product_id = self.request.query_params.get('product')
              if product_id:
                     return self.queryset.filter(product_id=product_id)
              return self.queryset


       @cache_response(key_prefix="product_variant_list",error_message="Unable to fetch Product Variant",allowed_params=[])
       def list(self, request,*args, **kwargs):
              response = super().list(request,*args, **kwargs)
              return response

       @cache_response(key_prefix="product_variant_detail", error_message="This Variant is not Avalible",allowed_params=[])
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
       
       http_method_names = ['get','put', 'patch', 'delete', 'head', 'options'] # only allow methods form this list . that means disabling the POST and the GET  list method not retrive

       def create(self, request, *args, **kwargs):
              product_id = request.data.get('product')
              user_id = request.user.id
              rating = request.data.get('rating')
              comment = request.data.get('comment')

              try:
                     add_review_process(product_id, user_id, rating, comment)
                     return Response({"detail": "Review submitted successful"}, status = status.HTTP_201_CREATED)
              except ValueError as e:
                     return Response({"detail": str(e)}, status = status.HTTP_400_BAD_REQUEST)

       @cache_response(key_prefix="review_list",error_message="Unable to show the Review",allowed_params=['product_id','page','rating','ordering'])
       def list(self,request,*args, **kwargs):
                
              response = super().list(request,*args, **kwargs)
             
              return response

       @cache_response(key_prefix="review_detail",error_message="Review Not Found",allowed_params=[])
       def retrieve(self, request, *args, **kwargs):
              
              instance = self.get_object()
              serializer = self.get_serializer(instance)
              data = serializer.data
              
              return Response(data)

       def update(self, request, *args, **kwargs):
              review_id = kwargs.get('pk')
              user_id = request.user.id
              rating = request.data.get('rating')
              comment = request.data.get('comment')
              try:
                     update_reveiw_process(review_id, user_id, rating, comment)
                     return Response({"detail": "Review updated successfully"}, status=status.HTTP_200_OK)
              except ValueError as e:
                     return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
              except PermissionError as e:
                     return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
