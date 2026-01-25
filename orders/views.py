from django.shortcuts import render
from rest_framework import viewsets , permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Order, OrderItem,ShippingAddress
from .serializers import OrderSerializer, OrderItemSerializer , ShippingAddressSerializer
# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
       serializer_class = OrderSerializer
       permission_classes = [permissions.IsAuthenticated]# need to login
       
       def get_queryset(self):
              return Order.objects.filter(user=self.request.user)#nsures the user can ONLY see their OWN orders. It hides everyone else's orders. If you didn't have this line, yes, they might see other people's data.
       @action(detail=False,methods =['post'])
       def add_to_cart(self,request):
              product_id = request.data.get('product_id')
              quantity = int(request.data.get('quantity',1))

              order, created = Order.objects.get_or_create(
                     user=request.user,
                     status = 'Cart'
              )

              item,created = OrderItem.objects.get_or_create(
                     order = order,
                     product_id = product_id
              )
              
              if not created:
                     item.quantity += quantity
              else:
                     item.quantity = quantity
              item.save()

              serializer = self.get_serializer(order)
              return Response(serializer.data)
       
       @action (detail=False,methods=['post'])#Update the Quantity (Set to Specific number)
       def update_quantity(self, request):
              product_id = request.data.get('product_id')
              quantity = int(request.data.get('quantity',1))#where we actuallying getting it from we are not only connected this vieweset to the order seializer and permisson classes
              order = Order.objects.get(user = request.user, status = 'Cart')
              try:
                     item = OrderItem.objects.get(order=order, product_id = product_id)
              except OrderItem.DoesNotExist:
                     return Response({"error ": "Item not in Cart"},status=status.HTTP_404_NOT_FOUND)
              if quantity < 1:
                     item.delete()
              else:
                     item.quantity = quantity
                     item.save()
              serializer = self.get_serializer(order)
              return Response(serializer.data)
              
              # Remove Item (Delete Completely )
       @action(detail=False, methods=['post'])
       def remove_item(self,request):
              product_id = request.data.get('product_id')#to whom . whom where requesting too for the data
              try:
                     order = Order.objects.get(user=request.user, status='Cart')
                     item = OrderItem.objects.get(order=order, product_id= product_id)
                     item.delete()
              except (Order.DoesNotExist, OrderItem.DoesNotExist):
                     return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
              
              serializer = self.get_serializer(order)# in this line what is get_serializer and what is order 
              return Response(serializer.data)
       @action(detail=False, methods=['post'])
       def checkout(self,request):
              address_id = request.data.get('address_id')
              
              try:
                     order = Order.objects.get(user=request.user,status = 'Cart')
              except Order.DoesNotExist:
                     return Response({'error': 'Cart is empty'}, status=status.HTTP_404_NOT_FOUND)
              
              try:
                     address = ShippingAddress.objects.get(id=address_id, user=request.user)
              except ShippingAddress.DoesNotExist:
                     return Response({'error': 'Invalid Address ID'}, status=status.HTTP_404_NOT_FOUND)
              order.shipping_address = address
              order.status = 'Pending'
              order.save()
              
              serializer = self.get_serializer(order)
              return Response(serializer.data)
              
class ShippingAddressViewSet(viewsets.ModelViewSet):
       serializer_class = ShippingAddressSerializer
       permission_classes = [permissions.IsAuthenticated]

       def get_queryset(self):
              return ShippingAddress.objects.filter(user=self.request.user)#only show USER address
       def perform_create(self, serializer):
              serializer.save(user=self.request.user) # auto-assign the logged-in use when saving 
              
                     
