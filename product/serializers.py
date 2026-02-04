from rest_framework import serializers
from .models import Category, Product, ProductImages, ProductVariant, Review

class  ReviewSerializer(serializers.ModelSerializer):
       user = serializers.StringRelatedField(read_only=True) # Show the user name insted of Id
       
       class Meta:
              model = Review
              fields = ['id','user','rating', 'comment', 'created_at']

#1. Serializer for Images (TO handle mutlipel uploads)

class ProdcutImageSerializer(serializers.ModelSerializer):
       class Meta:
              model = ProductImages
              fields = ['id', 'image','is_thumbnail']
# 2. Serial
class CategroySerializer(serializers.ModelSerializer):
       class Meta:
              model = Category
              fields = ['id','name','slug','image']
class ProductVarinatSerializer(serializers.ModelSerializer):
       class Meta:
              model = ProductVariant
              fields = ['id','product','size','color','price_adjustment','stock','is_active']
              
class ProductSerializer(serializers.ModelSerializer):
       #Read Only : Nested Serialzers for displaying full details in JSON
       category = CategroySerializer(read_only = True)
       images = ProdcutImageSerializer(many = True, read_only = True)
       variants = ProductVarinatSerializer(many=True, read_only = True)
       #Write Only: Fields to accept input when creating a product
       reviews = ReviewSerializer(many=True,read_only=True)
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
                     'description',
                     'price',
                     'stock',
                     'is_active',
                     'images',
                     'uploaded_images', # Read vs Write
                     'variants',
                     'reviews',
                     'average_rating',
                     'review_count'
              ]
              read_only_fields = ['slug','created_at','updated_at']
              
       def create(self,validate_data):
              # Pop the Image out (Product model doesn't handle them directily)
              uploaded_images = validate_data.pop('uploaded_images',[])
              # Create the Product (The Category_id is automatically handled by 'source=category')
              
              product = Product.objects.create(**validate_data)

              for image in uploaded_images:
                     ProductImages.objects.create(product=product,image=image)
              return product
       def get_average_rating(self,obj):
              #Calculate the average sum of of stars/ number of reviews
              reviews = obj.reviews.all()# explain this line 
              if reviews.exists():
                     return round(sum([r.rating for r in reviews])/ reviews.count(),1) # Question: what is the caculation method in here
              return 0
       def get_review_count(self,obj):# Question : what is method is for
              return obj.reviews.count()
       