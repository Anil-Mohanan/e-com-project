from rest_framework import serializers
from .models import Order , OrderItem, ShippingAddress
from datetime import timedelta

class OrderItemSerializer(serializers.ModelSerializer):
       product_name = serializers.CharField(source = 'product.name', read_only = True)
       #Use a MethodFeild to Safely get the image without Crasing
       product_image = serializers.SerializerMethodField()
       product_slug = serializers.ReadOnlyField(source = 'product.slug')

       class Meta:
              model = OrderItem
              fields = ['product_name','product_image','quantity','product_slug','price_at_purchase']
       def get_product_image(self,obj):
              # 1 Grab all images for the product
              #Note : 'images' is the related_name we typically assume.
              # if product model dind't set related_name = 'images', use 'productimage_set'

              images = obj.product.images.all()
              
              #2. check if any exist
              if images:
                     # 3. Return the URL of the first one
                     return images[0].image.url
              return None

class OrderSerializer(serializers.ModelSerializer):
       #nesting the OrderItem Serializer
       items = OrderItemSerializer(many = True, read_only = True)
       tax_amount = serializers.ReadOnlyField()
       shipping_fee = serializers.ReadOnlyField()
       subtotal = serializers.ReadOnlyField()
       total_price = serializers.ReadOnlyField() # this grabs the @property from the model
       estimated_delivery = serializers.SerializerMethodField()

       
       class Meta:
              model = Order
              fields = ['order_id','user','status','created_at', 'items','subtotal','tax_amount','shipping_fee','total_price','estimated_delivery']
       def get_estimated_delivery(self,obj):
              delivery_date = obj.created_at + timedelta(days=5)
              return delivery_date.date()
class ShippingAddressSerializer(serializers.ModelSerializer):
       class Meta:
              model = ShippingAddress
              fields = ['id', 'user', 'full_name', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country', 'phone_number', 'is_default']
              read_only_fields = ['user'] #User is set automatically 
              
              
