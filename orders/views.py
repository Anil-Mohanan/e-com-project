from django.shortcuts import render
from rest_framework import viewsets , permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction
from .models import Order, OrderItem,ShippingAddress
from .serializers import OrderSerializer, OrderItemSerializer , ShippingAddressSerializer
# Create your views here.

class OrderViewSet(viewsets.ModelViewSet):
       serializer_class = OrderSerializer
       permission_classes = [permissions.IsAuthenticated]# need to login
       
       lookup_field = 'order_id'
       def get_queryset(self):
              """Custom Login:
              -Admin: sees all the orders(the Dashboard)
              -Customer : sees only their own orders(Order History)."""
              user = self.request.user
              if user.is_staff:# checks if the user is Admin / Staff
                     return Order.objects.all().order_by('-created_at')
              return Order.objects.filter(user=user).order_by('-created_at') # ensuring that the loged in user only sees only his orders

                     
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
              quantity = int(request.data.get('quantity',1))
              
              try:
                     order = Order.objects.get(user = request.user, status = 'Cart')
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
              serializer = self.get_serializer(data = request.data)
              

              address_id = request.data.get('address_id')

              try:
                     with transaction.atomic():
                            #Get the cart
                            order = Order.objects.get(user=request.user, status = 'Cart')
                            # Get the Address
                            address = ShippingAddress.objects.get(id = address_id, user = request.user)

                            items = order.items.select_related('product')#It allows you to walk backwards from the Parent (Order) to the Children (OrderItems), even though the Parent doesn't actually store the Children's IDs.
                            
                            for item in items:
                                   product = item.product
                                   
                                   if product.stock < item.quantity:
                                          raise ValueError(f"Sorry,{product.name} is out of stock (Only {product.stock} left).")
                                   product.stock -= item.quantity
                                   product.save()
                                   item.price_at_purchase = product.price # Saving the price now so if the changes later , the order history is correct
                                   
                                   item.save()
                                   
                            order.shipping_address = address
                            order.status = 'Pending'
                            order.save()
                            
                            return Response(self.get_serializer(order).data)
              except Order.DoesNotExist:
                     return Response({'error': 'Cart is empty'}, status=status.HTTP_404_NOT_FOUND)
              except ShippingAddress.DoesNotExist:
                     return Response({'error': 'Invalid Address ID'}, status=status.HTTP_404_NOT_FOUND)
              except ValueError as e:
                     return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
       @action(detail=False, methods=['get'])
       def cart(self,request):
              """Fethc the current user's active cart.
              if it doesn't exist, create a new one."""

              order, created = Order.objects.get_or_create(
                     user= request.user,
                     status = 'Cart'
              )
              serializer = self.get_serializer(order)
              return Response(serializer.data)
       @action(detail=True, methods=['patch'])
       def update_status(self,request,pk=None):
              """only Admin Can change the order status(e.g, Pending, shipped)"""
              
              #Security Check: Are you Admin
              if not request.user.is_staff:
                     return Response({'error': 'Only admins Can update status'}, status=status.HTTP_403_FORBIDDEN)
              order = self.get_object()
              new_status = request.data.get('status')

              if new_status not in dict(Order.ORDER_STATUS):
                     return Response({'error':'Invalid status'},status=status.HTTP_400_BAD_REQUEST)
              
              order.status = new_status
              order.save()
              return Response({'status': 'Order updated', 'current_status':order.status})
       @action(detail=True, methods=['post'])
       def cancel_order(self,request,pk=None):
              """Allow user to Cancel their OWN order.
              critical: This must restore the stock on the products!"""

              order = self.get_object()
              
              #1. Validation: Can we actually cancel this 
              if order.status != 'Pending':
                     return Response(
                            {'error': 'Cannot Cancel order . It might be already Shipped or deliverd'},
                            status=status.HTTP_400_BAD_REQUEST
                            )
              try: 
                     with transaction.atomic():
                            #Resotre Stock
                            items = order.items.select_related('product')
                            for item in items:
                                   product = item.product
                                   product.stock += item.quantity# Add it back!
                                   product.save()
                            order.status = 'Cancelled'
                            order.save()
                            
                            return Response({'status': 'Order cancelled Successfully','new_status': 'Cancelled'})
              except Exception as e:
                     return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                                          
       
class ShippingAddressViewSet(viewsets.ModelViewSet):
       serializer_class = ShippingAddressSerializer
       permission_classes = [permissions.IsAuthenticated]

       def get_queryset(self):
              return ShippingAddress.objects.filter(user=self.request.user)#only show USER address
       def perform_create(self, serializer):
              serializer.save(user=self.request.user) # auto-assign the logged-in use when saving 
              
                     
