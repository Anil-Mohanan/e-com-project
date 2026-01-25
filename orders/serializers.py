from rest_framework import serializers
from .models import Order , OrderItem, ShippingAddress

class OrderItemSerializer(serializers.ModelSerializer):
       product_name = serializers.CharField(source = 'product.name', read_only = True)
       product_image = serializers.CharField(source = 'product.image.first.image.url',read_only = True)

       class Meta:
              model = OrderItem
              fields = ['product_name','product_image','quantity','price_at_purchase']

class OrderSerializer(serializers.ModelSerializer):
       #nesting the OrderItem Serializer
       items = OrderItemSerializer(many = True, read_only = True)
       tax_amount = serializers.ReadOnlyField()
       shipping_fee = serializers.ReadOnlyField()
       total_price = serializers.ReadOnlyField() # this grabs the @property from the model
       
       class Meta:
              model = Order
              fields = ['id','user','status','created_at', 'items','subtotal','tax_amount','shipping_fee','total_price']

class ShippingAddressSerializer(serializers.ModelSerializer):
       class Meta:
              model = ShippingAddress
              fields = ['id', 'user', 'full_name', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country', 'phone_number', 'is_default']
              read_only_fields = ['user'] #User is set automatically 
              
              
