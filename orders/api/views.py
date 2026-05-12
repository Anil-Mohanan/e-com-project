from rest_framework import viewsets , permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from orders.models import Order, OrderItem,ShippingAddress
from .serializers import OrderSerializer, OrderItemSerializer , ShippingAddressSerializer, CartSerializer,CheckoutInputSerializer
from django.core.cache import cache
from config.cache_utils import cache_response, invalidate_cache
from config.utils import error_response,success_response
from orders.services import process_checkout, add_to_cart_process,update_quantity_process,remove_item_process,update_status_process,cancel_order_process,mark_as_paid_process,sync_order_prices,get_user_cart
from rest_framework.throttling  import UserRateThrottle
from rest_framework import viewsets, permissions, mixins
from django.core.exceptions import ObjectDoesNotExist
import logging



logger = logging.getLogger(__name__)
class CheckoutThrottle(UserRateThrottle):
       rate = '200/minute'

class CartViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
       permission_classes = [permissions.IsAuthenticated]
       serializer_class = CartSerializer

       def get_queryset(self):
              return Order.objects.filter(user=self.request.user, status='Cart')

       @action(detail=False,methods =['post'])
       def add_to_cart(self, request, *args, **kwargs):

              #"This is intentionally NOT idempotent. Repeated calls increment quantity, which matches standard e-commerce UX. For strict API idempotency, the client should use update_quantity with an absolute value instead."

              product_id = request.data.get('product_id')

              quantity = int(request.data.get('quantity',1))
              try:
                     order = add_to_cart_process(
                            user=request.user,
                            product_id=product_id,
                            quantity=quantity,
                     )
                     
              except ObjectDoesNotExist:
                     return error_response(message = "Product not found",status_code=404)

              order_model = Order.objects.get(order_id=order.order_id)
              serializer = self.get_serializer(order_model)
              invalidate_cache("user_cart")
              return Response(serializer.data)

       
       @cache_response(key_prefix="user_cart",timeout=60, user_specific=True,error_message="Unable to Load your cart", allowed_params=[])
       def list(self, request, *args, **kwargs):
              """Fetch the current user's active cart.
              if it doesn't exist, create a new one."""

              order = get_user_cart(request.user)
              
              sync_order_prices(order.order_id)

              order_model = Order.objects.get(order_id=order.order_id)
              serializer = self.get_serializer(order_model)

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
                     return error_response(message = "Item not in Cart",status_code = 404)

              order_model = Order.objects.get(order_id=order.order_id)
              serializer = self.get_serializer(order_model)
              invalidate_cache("user_cart")
              return Response(serializer.data)

                     # Remove Item (Delete Completely )
       @action(detail=False, methods=['post'])
       def remove_item(self, request, *args, **kwargs):

              product_id = request.data.get('product_id')

              try:
                     order = remove_item_process(
                            user = request.user,
                            product_id = product_id,
                     )
                     
              except (Order.DoesNotExist, OrderItem.DoesNotExist):
                     return error_response(message = 'Item  Not Found', status_code = 404)
              
              order_model = Order.objects.get(order_id=order.order_id)
              serializer = self.get_serializer(order_model)
              invalidate_cache("user_cart")
              return Response(serializer.data)


class CheckoutViewSet(viewsets.GenericViewSet):
       permission_classes = [permissions.IsAuthenticated]
       serializer_class = OrderSerializer
       throttle_classes = [CheckoutThrottle]

       lookup_field = 'order_id'

       def create(self, request, *args, **kwargs):
              serializer = CheckoutInputSerializer(data = request.data)
              serializer.is_valid(raise_exception=True)

              address_id = serializer.validated_data['address_id']
              product_ids = serializer.validated_data['product_ids']

              try:
                     order = process_checkout(user = request.user, address_id= address_id,product_ids =product_ids)
                     order_model = Order.objects.get(order_id=order.order_id)
                     invalidate_cache("user_orders")
                     invalidate_cache("user_cart")
                     return Response(self.get_serializer(order_model).data)
                     
              except Order.DoesNotExist:
                     return error_response(message =  'no cart and no pending order', status_code = 404)
              except ShippingAddress.DoesNotExist:
                     return error_response(message = 'Invalid Address ID', status_code = 404)
              except ValueError as e:
                     status_code = 404 if "not found" in str(e).lower() else 400
                     return error_response(message=str(e),status_code=status_code)
       
class OrderHistoryViewset(viewsets.ReadOnlyModelViewSet):

       permission_classes = [permissions.IsAuthenticated]
       serializer_class = OrderSerializer
       lookup_field = 'order_id'
       def get_queryset(self):
              queryset = Order.objects.select_related('user').prefetch_related('items')
              user = self.request.user
              return queryset.for_user(user).exclude(status = 'Cart').order_by('-created_at')

       @cache_response(key_prefix="user_orders", timeout=300, user_specific=True, error_message="Unable to load your Orders at this time",allowed_params=['page','status'])
       def list(self,request,*args, **kwargs):
              return super().list(request,*args, **kwargs)                    
       
       @cache_response(key_prefix="Order_detail", timeout=900, user_specific=True, error_message="Order Not Found",allowed_params=[])
       def retrieve(self, request, *args, **kwargs):
              instance = self.get_object()
              serializer = self.get_serializer(instance)
              data = serializer.data
              return Response(data)

       @action(detail=True, methods=['post'])
       def cancel_order(self,request,order_id = None,**kwargs):
              """Allow user to Cancel their OWN order.
              critical: This must restore the stock on the products!"""

              order = self.get_object()
              
              
              #1. Validation: Can we actually cancel this 
              if order.status not in ['Pending','OrderConfirmed']:
                     return error_response(message="Cannot Cancel order. It might be already Shipped or deliverd",status_code=400)
              try:
                     order = cancel_order_process(
                     order_id = order.order_id
                     )
                     invalidate_cache("user_orders")
                     invalidate_cache('Order_detail')
                     return success_response(message="Order cancelled Successfully",data={'new_status': 'cancelled'},status_code=200)
              except Exception as e:
                     return error_response(message =  str(e), status_code = 500)
                     



class AdminOrderViewSet(viewsets.ModelViewSet):
       lookup_field = 'order_id'
       permission_classes = [permissions.IsAdminUser]
       serializer_class = OrderSerializer

       def get_queryset(self):
              queryset = Order.objects.all()
              return queryset.exclude(status='Cart').order_by('-created_at')

       @action(detail=True, methods=['patch'])
       def update_status(self,request,order_id = None,**kwargs):
              """only Admin Can change the order status(e.g, Pending, shipped)"""
                     
              order = self.get_object()
              new_status = request.data.get('status')

              if new_status not in dict(Order.ORDER_STATUS):
                     return error_response(message = "Invalid Status",status_code = 400)
              
              order = update_status_process(
                     order_id = order.order_id,
                     new_status = new_status,
                     actor = request.user,
              )
              invalidate_cache("user_orders")
              invalidate_cache("Order_detail")
              return success_response(message = "Order updated Successfully",data ={'current_status':order.status})
       
       @action(detail=True, methods=['patch'])
       def mark_as_paid(self,request, order_id = None,**kwargs):
              """Manal Pay by the Admin to Mark an order is paid Use full of COD"""
              
              if not request.user.is_staff:
                     return error_response(message="Only Admin Can change the status",status_code=400) 

              order = self.get_object()
              
              #check if already paid
              if order.is_paid:
                     return success_response(message="Order is already Paid")

              mark_as_paid_process(order_id=order.order_id)
              invalidate_cache("user_orders")
              invalidate_cache("Order_detail")
              
              return success_response(message = "Payment confirmed",data ={'isPaid': True})


class ShippingAddressViewSet(viewsets.ModelViewSet):
       serializer_class = ShippingAddressSerializer
       permission_classes = [permissions.IsAuthenticated]
       
       # lookup_field ='user'  <-- This was broken. Use default 'pk' for individual addresses.
       def get_queryset(self):
              return ShippingAddress.objects.filter(user=self.request.user)#only show USER address
       def perform_create(self, serializer):
              serializer.save(user=self.request.user) # auto-assign the logged-in use when saving 

       @cache_response(key_prefix="user_address", timeout=300, user_specific=True, error_message="Unable to Load Your Address At This time",allowed_params=[])
       def list(self,request,*args, **kwargs):
              return super().list(request,*args, **kwargs)

       @cache_response(key_prefix="Address_details", timeout=300, user_specific=True, error_message="Unable to Retrieve Address Details",allowed_params=[])
       def retrieve(self, request, *args, **kwargs):
              instance = self.get_object()
              serializer= self.get_serializer(instance)
              data = serializer.data 
              return Response(data)

                     