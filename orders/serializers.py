from rest_framework import serializers
from .models import Order , OrderItem, ShippingAddress
from datetime import timedelta

class OrderItemSerializer(serializers.ModelSerializer):
       product_name = serializers.CharField(read_only = True)

       class Meta:
              model = OrderItem
              fields = ['product_id','product_name','quantity','price_at_purchase']



class ShippingAddressSerializer(serializers.ModelSerializer):
       class Meta:
              model = ShippingAddress
              fields = ['id', 'user', 'full_name', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country', 'phone_number', 'is_default']
              read_only_fields = ['user'] #User is set automatically


class OrderSerializer(serializers.ModelSerializer):
       #nesting the OrderItem Serializer
       items = OrderItemSerializer(many = True, read_only = True)
       shipping_address = ShippingAddressSerializer(read_only = True)
       tax_amount = serializers.ReadOnlyField()
       shipping_fee = serializers.ReadOnlyField()
       subtotal = serializers.ReadOnlyField()
       total_price = serializers.ReadOnlyField() # this grabs the @property from the model
       estimated_delivery = serializers.SerializerMethodField()

       
       class Meta:
              model = Order
              fields = ['order_id','user','status','created_at', 'items','shipping_address','is_paid','paid_at','subtotal','tax_amount','shipping_fee','total_price','estimated_delivery']
       def get_estimated_delivery(self,obj):
              delivery_date = obj.created_at + timedelta(days=5)
              return delivery_date.date()
 
              
              
