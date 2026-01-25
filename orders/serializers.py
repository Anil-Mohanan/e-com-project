from rest_framework import serializers
from .models import Order , OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
       product_name = serializers.CharField(source = 'product.name', read_only = True)
       product_image = serializers.CharField(source = 'product.image.first.image.url',read_only = True)

       class Meta:
              model = OrderItem
              fields = ['product_name','product_image','quantity','price_at_purchase','total_price']

class OrderSerializer(serializers.ModelSerializer):
       #nesting the OrderItem Serializer
       items = OrderItemSerializer(many = True, read_only = True)

       total_price = serializers.ReadOnlyField() # this grabs the @property from the model
       
       class Meta:
              model = Order
              fields = ['id','user','status','total_price', 'created_at', 'items']
       
