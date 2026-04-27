from orders.models import Order, OrderItem , ShippingAddress, OrderEventOutbox
from orders.domain import OrderItemEntity, OrderEntity, OrderEventEntity, OrderEmailDTO, OrderEmailItemDTO
from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.db import transaction
from django.utils import timezone


# -------------- CONVERTERS ----------------- #

def _to_entity(order):

       items = order.items.all()

       item_entites = []

       for item in items:

              entity = OrderItemEntity(

                     product_id = item.product_id,
                     variant_id = item.variant_id,
                     product_name = item.product_name,
                     quantity = item.quantity,
                     price_at_purchase = item.price_at_purchase
              )

              item_entites.append(entity)

       return OrderEntity(

              order_id = str(order.order_id),
              user_id = order.user_id,
              status = order.status,
              is_paid = order.is_paid,
              paid_at = order.paid_at,
              items = item_entites
       )

# ------------- ORDER READS ----------- #

def get_cart(user) -> OrderEntity:
       try:
              cart = Order.objects.current_cart(user).get()
              return _to_entity(cart)
       except Order.DoesNotExist:
              raise ValueError("Order not found")

def get_or_create_cart(user) -> tuple[OrderEntity, bool]:
       
       cart, created = Order.objects.get_or_create_cart(user)
       return _to_entity(cart), created
     

def get_order_by_id(order_id) -> OrderEntity:
       try:
              order = Order.objects.get(order_id = order_id)
              return _to_entity(order)
       except Order.DoesNotExist:
              raise ValueError("Order not Found")

def get_pending_order_for_user(user_id):

       order = Order.objects.filter(status = "Pending", user_id = user_id).order_by('-created_at').first()

       if order:
              return  _to_entity(order)
       else:
              return None

def get_order_for_user(order_id,user_id):

       try:
              order = Order.objects.get(order_id = order_id, user_id = user_id)
              return _to_entity(order)
       except Order.DoesNotExist:
              raise ValueError("Order not Found")

def get_order_items_data(order_id):
       try:
              order = Order.objects.get(order_id = order_id)

              return [{"product_id": item.product_id, "quantity": item.quantity} for item in order.items.all()]
       except Order.DoesNotExist:
              raise ValueError("Order not found")

def get_unpaid_pending_orders(cutoff_time):
       orders = Order.objects.filter(status = "Pending", created_at_lte = cutoff_time)
       return [_to_entity(order) for order in orders]

def get_order_email_data(order_id) -> OrderEmailDTO:

       try:
              order = Order.objects.select_related('user', 'shipping_address').prefetch_related('items__product').get(order_id=order_id)

       except Order.DoesNotExist:
              raise ValueError("Order Not Found")

       items_dto = [
              OrderEmailItemDTO(product_name = item.product.name,quantity=item.quantity)
              for item in order.items.all()
       ]
       payment_method = "Cod/Online"
       if hasattr(order, 'payment') and order.payment:
              payment_method = order.payment.payment_method
       
       return OrderEmailDTO(
       order_id=str(order.order_id),
       first_name=order.user.first_name,
       email=order.user.email,
       total_price=order.total_price,
       status=order.status,
       items=items_dto,
       address_line_1=order.shipping_address.address_line_1 if hasattr(order, 'shipping_address') and order.shipping_address else None,
       city=order.shipping_address.city if hasattr(order, 'shipping_address') and order.shipping_address else None,
       payment_method=payment_method
       )

       
#------------ ORDER WRITES ---------- #

def save_order_status(order_id, new_status):
       try:
              order = Order.objects.get(order_id = order_id)
              order.status = new_status
              order.save()
       except Order.DoesNotExist:
              raise ValueError("There is no Order to Save status")

def mark_order_paid(order_id):
       with transaction.atomic():
              try:
                     order = Order.objects.get(order_id = order_id)
                     order.paid_at = timezone.now()
                     order.is_paid = True
                     order.save()
                     return _to_entity(order)
              except Order.DoesNotExist:
                     raise ValueError("There is not Order for to pay")

def checkout_order(order_id, address_id, user):

       with transaction.atomic():
              
              try:
                     order = Order.objects.get(order_id = order_id)

                     address = ShippingAddress.objects.get(user = user,id = address_id)

                     order.shipping_address = address

                     order.status = "Pending"

                     order.save()
              except (Order.DoesNotExist, ShippingAddress.DoesNotExist):
                     raise ValueError("Order or shipping address not found")


# -------------ITEM OPERATIONS ------------- #

def add_item_to_cart(order_id, product_id, product_name, quantity):

       with transaction.atomic():
              try:
                     order = Order.objects.get(order_id = order_id)

                     item , created = OrderItem.objects.get_or_create(order = order,product_id = product_id, defaults = {'product_name': product_name})  

                     if not created:
                            item.quantity += quantity
                     else:
                            item.quantity = quantity

                     item.save()
                     order.save()


                     return item.id, created
              except Order.DoesNotExist:
                     raise ValueError("NO ORDER FOUND")

def update_item_quantity(order_id,product_id,quantity):

       with transaction.atomic():
              try:
                     order = Order.objects.get(order_id = order_id)
                     item  = OrderItem.objects.get(order = order,product_id = product_id)
                     if quantity < 1:     
                            item.delete()
                     else:
                            item.quantity = quantity
                            item.save()
                     order.save()

                     return _to_entity(order)
              except (Order.DoesNotExist, OrderItem.DoesNotExist):
                     raise ValueError("Order or item not found")

def delete_item(order_id,product_id):

       with transaction.atomic():
              try:
                     order = Order.objects.get(order_id = order_id)

                     item  = OrderItem.objects.get(order = order,product_id = product_id)

                     item.delete()
                     order.save()
                     return _to_entity(order)
              except (Order.DoesNotExist, OrderItem.DoesNotExist):
                     raise ValueError("Order or item not found")

def set_item_price(order_id,product_id,price):
       try:
              order = Order.objects.get(order_id = order_id)

              item  = OrderItem.objects.get(order = order,product_id = product_id)

              item.price_at_purchase = price
              item.save()
       except (Order.DoesNotExist, OrderItem.DoesNotExist):
              raise ValueError("Order or item not found")



# ------------- EVENT OPERATIONS ------------- #

def create_outbox_event(event_type: str, payload: dict):

       order_event = OrderEventOutbox.objects.create(event_type = event_type,payload = payload)

def get_unprocessed_outbox_events():

       events = OrderEventOutbox.objects.filter(processed = False, retry_count__lt = 5).order_by('created_at')

       return [
              OrderEventEntity(id = e.id, event_type=e.event_type, payload=e.payload) for e in events
       ]

def mark_outbox_event_processed(event_id):

       event = OrderEventOutbox.objects.get(id = event_id)
       event.processed = True
       event.processed_at = timezone.now()
       event.save()

def mark_outbox_event_failed(event_id,error_messgae):

       event = OrderEventOutbox.objects.get(id = event_id)
       event.error_message = str(error_messgae)
       event.retry_count += 1
       event.save()

# ------------ ANALYTIC READS ------------- #

def get_dashboard_order_metrics():
       valid_orders = Order.objects.valid_sales()
       total_orders = valid_orders.count()
       revenue_data = valid_orders.aggregate(Sum('total_price'))
       total_revenue  = revenue_data['total_price__sum'] or 0
       

       return {"total_orders" : total_orders,"total_revenue": total_revenue}

def get_daily_sales_chart_data():
       valid_orders = Order.objects.valid_sales()
       sale_data = list(valid_orders.annotate(date = TruncDate('created_at')).values('date').annotate(total = Sum('total_price')).order_by('date'))
       return sale_data

def get_monthly_sales_chart_data():
       valid_orders = Order.objects.valid_sales()
       sale_data = list(valid_orders.annotate(date = TruncMonth('created_at')).values('date').annotate(total = Sum('total_price')).order_by('date'))
       return sale_data

def get_top_selling_products():
       # ONLY pulls top selling. Queries OrderItem. Wraps in list() instantly.
       top_products = OrderItem.objects.top_selling()
       return list(top_products) 

