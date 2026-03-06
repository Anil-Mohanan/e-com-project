from django.shortcuts import render
from rest_framework import viewsets , permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Order, OrderItem,ShippingAddress
from .serializers import OrderSerializer, OrderItemSerializer , ShippingAddressSerializer
from product.models import Product
from .emails import send_order_confirmation_email, send_shipping_email, send_cancellation_email,send_payment_success_email
from datetime import datetime
from django.core.cache import cache
from config.cache_utils import cache_response
from config.utils import error_response
from .services import process_checkout, add_to_cart_process,update_quantity_process,remove_item_process,update_status_process,cancel_order_process,mark_as_paid_process
import logging


logger = logging.getLogger(__name__)
class OrderViewSet(viewsets.ModelViewSet):
       serializer_class = OrderSerializer
       permission_classes = [permissions.IsAuthenticated]# need to login
       
       lookup_field = 'order_id'
       def get_queryset(self):
              """Custom Login:
              -Admin: sees all the orders(the Dashboard)
              -Customer : sees only their own orders(Order History)."""
              queryset = Order.objects.select_related('user').prefetch_related('items__product__images')
              user = self.request.user
              if user.is_staff:# checks if the user is Admin / Staff
                     return queryset.order_by('-created_at')
              return queryset.for_user(user).order_by('-created_at') # ensuring that the loged in user only sees only his orders

                     
       @action(detail=False,methods =['post'])
       def add_to_cart(self, request, *args, **kwargs):

              product_id = request.data.get('product_id')

              quantity = int(request.data.get('quantity',1))

              order,item = add_to_cart_process(
                     user=request.user,
                     product_id=product_id,
                     quantity=quantity,
              )

              serializer = self.get_serializer(order)

              cache.delete(f"user_cart_{request.user.id}")

              return Response(serializer.data)
       
       @action (detail=False,methods=['post'])#Update the Quantity (Set to Specific number)
       def update_quantity(self, request, *args, **kwargs):
              
              product_id = request.data.get('product_id')
              quantity = int(request.data.get('quantity',1))
              try:
                     order,item = update_quantity_process(
                            user= request.user,
                            product_id = product_id,
                            quantity = quantity
                     )
              except OrderItem.DoesNotExist:
                     return Response({"error ": "Item not in Cart"},status=status.HTTP_404_NOT_FOUND)

              serializer = self.get_serializer(order)
              cache.delete(f"user_cart_{request.user.id}")
              return Response(serializer.data)
              
              # Remove Item (Delete Completely )
       @action(detail=False, methods=['post'])
       def remove_item(self, request, *args, **kwargs):

              product_id = request.data.get('product_id')#to whom . whom where requesting too for the data

              try:
                     order = remove_item_process(
                            user = request.user,
                            product_id = product_id,
                     )
              except (Order.DoesNotExist, OrderItem.DoesNotExist):
                     return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
              
              serializer = self.get_serializer(order)# in this line what is get_serializer and what is order 
              cache.delete(f"user_cart_{request.user.id}")
              return Response(serializer.data)
       
       @action(detail=False, methods=['post'])
       def checkout(self, request, *args, **kwargs):
              serializer = self.get_serializer(data = request.data)
              
              address_id = request.data.get('address_id')

              try:
                     order = process_checkout(user = request.user, address_id= address_id)
                     return Response(self.get_serializer(order).data)
                     
              except Order.DoesNotExist:
                     return Response({'error': 'Cart is empty'}, status=status.HTTP_404_NOT_FOUND)
              except ShippingAddress.DoesNotExist:
                     return Response({'error': 'Invalid Address ID'}, status=status.HTTP_404_NOT_FOUND)
              except ValueError as e:
                     return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
       

       @action(detail=False, methods=['get'])
       @cache_response(key_prefix="user_cart", timeout=60, user_specific=True, error_message="Unable to load your cart")
       def cart(self, request, *args, **kwargs):
              """Fethc the current user's active cart.
              if it doesn't exist, create a new one."""
              order, created = Order.objects.get_or_create_cart(request.user)
              serializer = self.get_serializer(order)
              return Response(serializer.data)

       @action(detail=True, methods=['patch'])
       def update_status(self,request,order_id = None):
              """only Admin Can change the order status(e.g, Pending, shipped)"""
                     
              #Security Check: Are you Admin
              if not request.user.is_staff:
                     return Response({'error': 'Only admins Can update status'}, status=status.HTTP_403_FORBIDDEN)
              order = self.get_object()
              new_status = request.data.get('status')

              if new_status not in dict(Order.ORDER_STATUS):
                     return Response({'error':'Invalid status'},status=status.HTTP_400_BAD_REQUEST)
              
              order = update_status_process(
                     order = order,
                     new_status = new_status
              )
              
              return Response({'status': 'Order updated', 'current_status':order.status})

       @action(detail=True, methods=['post'])
       def cancel_order(self,request,order_id = None):
              """Allow user to Cancel their OWN order.
              critical: This must restore the stock on the products!"""

              order = self.get_object()
              
              
              #1. Validation: Can we actually cancel this 
              if order.status != 'Pending':
                     return Response(
                            {'error': 'Cannot Cancel order . It might be already Shipped or deliverd'},status=status.HTTP_400_BAD_REQUEST)
              try:
                     order = cancel_order_process(
                     order = order
                     )
                     return Response({'status': 'Order cancelled Successfully','new_status': 'Cancelled'})
              except Exception as e:
                     return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                     
       @action(detail=True, methods=['patch'])
       def mark_as_paid(self,request, order_id =None):
              """Manal Pay by the Admin to Mark an order is paid Use full of COD"""
              
              if not request.user.is_staff:
                     return Response({'error': 'Admins Only'}, status=status.HTTP_400_BAD_REQUEST)

              order = self.get_object()
              
              #check if already paid
              if order.is_paid:
                     return Response({'message': 'order is already paid'})

              mark_as_paid_process(order=order)
              
              return Response({'status': 'Payment confirmed','isPaid': True})
       
       
       
       @cache_response(key_prefix="user_orders", timeout=300, user_specific=True, error_message="Unable to load your Orders at this time")
       def list(self,request,*args, **kwargs):
              return super().list(request,*args, **kwargs)                    
       
       @cache_response(key_prefix="Order_detail", timeout=900, user_specific=True, error_message="Order Not Found")
       def retrieve(self, request, *args, **kwargs):
              instance = self.get_object()
              serializer = self.get_serializer(instance)
              data = serializer.data
              return Response(data)

                     
       
class ShippingAddressViewSet(viewsets.ModelViewSet):
       serializer_class = ShippingAddressSerializer
       permission_classes = [permissions.IsAuthenticated]
       lookup_field ='user'
       def get_queryset(self):
              return ShippingAddress.objects.filter(user=self.request.user)#only show USER address
       def perform_create(self, serializer):
              serializer.save(user=self.request.user) # auto-assign the logged-in use when saving 

       @cache_response(key_prefix="user_address", timeout=300, user_specific=True, error_message="Unable to Load Your Address At This time")
       def list(self,request,*args, **kwargs):
              return super().list(request,*args, **kwargs)

       @cache_response(key_prefix="Address_details", timeout=300, user_specific=True, error_message="Unable to Retrieve Address Details")
       def retrieve(self, request, *args, **kwargs):
              instance = self.get_object()
              serializer= self.get_serializer(instance)
              data = serializer.data 
              return Response(data)

                     