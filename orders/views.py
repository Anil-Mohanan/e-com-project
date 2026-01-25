from django.shortcuts import render
from rest_framework import viewsets , permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderItemSerializer
# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
       serializer_class = OrderSerializer
       permission_classes = [permissions.IsAuthenticated]# need to login
       
       def get_queryset(self):
              return Order.objects.filter(user=self.request.user)# this override the defualt 'get all'. it ensures that the loged in user can see other people's orders
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
       
              