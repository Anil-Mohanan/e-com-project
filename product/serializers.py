from rest_framework import serializers
from .models import Category, Product, ProductImages

class ProdcutImageSerializer(serializers.ModelSerializer):
       class Meta:
              model = ProductImages
              fields = ['id', 'image','is_thumbnail']

class CategroySerializer(serializers.ModelSerializer):
       class Meta:
              model = Category
              fields = ['id','name','slug','image']
class ProductSerializer(serializers.ModelSerializer):
       #Nested Serializers: to show the Category details And the images inside the Product JSON
       category = CategroySerializer(read_only = True)
       images = ProdcutImageSerializer(many = True, read_only = True)

       class Meta:
              model = Product
              fields = [
                     'id',
                     'category',
                     'name',
                     'slug',
                     'description',
                     'price',
                     'stock',
                     'images'
              ]