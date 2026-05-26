from dataclasses import fields
from unicodedata import decimal
from rest_framework import serializers
from product.models import Category, Product, ProductImages, ProductVariant, Review, Color
from django.core.exceptions import ValidationError

class  ReviewSerializer(serializers.ModelSerializer):
       user = serializers.StringRelatedField(read_only=True) # Show the user name insted of Id
       
       class Meta:
              model = Review
              fields = ['id','user','rating', 'comment', 'created_at','product']

       def validate_comment(self,value):
              if  "<" in value or ">" in value:
                     raise serializers.ValidationError("Comments Cannot contain HTML Tags.")
              return value


class ColorSerializer(serializers.ModelSerializer):
       class Meta:
              model = Color
              fields = ['id','name','hex_code']


#1. Serializer for Images (TO handle mutlipel uploads)
class ProdcutImageSerializer(serializers.ModelSerializer):
       color = ColorSerializer(read_only =True)
       class Meta:
              model = ProductImages
              fields = ['id', 'image', 'is_thumbnail', 'is_primary', 'color', 'variant']
# 2. Serial
class CategorySerializer(serializers.ModelSerializer):
       # Including a list of products beloginig to this category
       products = serializers.SerializerMethodField()

       class Meta:
              model = Category
              fields = ['id','name','slug','image','required_specs_keys','metadata','products']

       def get_products(self, obj):
              # only active products of this Category
              products = obj.products.filter(is_active=True)[:10]
              from .serializers import ProductSerializer 
              return ProductSerializer(products, many  = True).data

class ProductVariantSerializer(serializers.ModelSerializer):
       product_slug = serializers.ReadOnlyField(source = 'product.slug')
       color = ColorSerializer(read_only = True)
       color_id = serializers.PrimaryKeyRelatedField(queryset = Color.objects.all(),source = 'color',write_only = True, required = False, allow_null = True)
       class Meta:
              model = ProductVariant
              fields = ['id','product','product_slug','sku','color','color_id','attributes','description','price','stock','is_active']
              
class ProductSerializer(serializers.ModelSerializer):
       #Read Only : Nested Serialzers for displaying full details in JSON
       category = serializers.StringRelatedField(read_only = True)
       category_id = serializers.PrimaryKeyRelatedField(
              queryset = Category.objects.all(),
              source = 'category',
              write_only = True
       )
       images = ProdcutImageSerializer(many = True, read_only = True)
       variants = ProductVariantSerializer(many=True, read_only = True)
       #Write Only: Fields to accept input when creating a product
       # reviews = ReviewSerializer(many=True,read_only=True)
       average_rating = serializers.SerializerMethodField()
       review_count = serializers.SerializerMethodField()
       category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        source='category', 
        write_only=True)  
       
       uploaded_images = serializers.ListField(child=serializers.ImageField(max_length = 100000, allow_empty_file = False, use_url = False),write_only = True, required = False)
       
       class Meta:
              model = Product
              fields = [
                     'id',
                     'category',
                     'category_id', # Read vs Write
                     'name',
                     'slug',
                     'brand',
                     'description',
                     'price',
                     'stock',
                     'is_active',
                     'images',
                     'uploaded_images', # Read vs Write
                     'variants',
                     'average_rating',
                     'review_count',
                     'specifications',
                     'base_attribute_name',
                     'base_attribute_value',
                     'created_at',
              ]
              read_only_fields = ['slug','created_at','updated_at']
              
       def create(self,validate_data):
              # Pop the Image out (Product model doesn't handle them directily)
              uploaded_images =  validate_data.pop('uploaded_images',[])
              # Create the Product (The Category_id is automatically handled by 'source=category')
              
              product = Product.objects.create(**validate_data)

              for image in uploaded_images:
                     ProductImages.objects.create(product=product,image=image)
              return product
       def get_average_rating(self,obj):
             return getattr(obj,'average_rating',0)or 0
       def get_review_count(self,obj):# Question : what is method is for
              return getattr(obj, 'review_count',0)

       def validate(self,attrs):
              category = attrs.get('category')
              specifications = attrs.get('specifications',{})

              if category and category.required_specs_keys:

                     for key in category.required_specs_keys:
                            if key not in specifications:
                                   raise serializers.ValidationError({"specifications" : f"Missing required specifications {key}"})
              return attrs

              
class ProductSearchSerializer(serializers.Serializer):
       """A ultra lean serializer for the instant search dropdown"""

       id = serializers.IntegerField()
       name = serializers.CharField()
       price = serializers.DecimalField(max_digits = 10, decimal_places = 2)
       slug = serializers.CharField()
       brand = serializers.CharField()
       image = serializers.SerializerMethodField()

       def get_image(self, obj):
              # The obj is dict from reids
              image_path = obj.get('image')
              if not image_path:
                     return None
              
              #Using request from the context to build an absolute URL
              request = self.context.get('request')
              if request:
                     return request.build_absolute_uri(f"/media/{image_path}")
                     return f"/media/{image_path}"