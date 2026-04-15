from .models import ShippingAddress, Order, OrderItem, OrderEventOutbox
from product.services import get_product_details
from django.db import transaction
from .tasks import (
       task_send_payment_success_email,
       task_send_order_confirmation_email,
       task_send_shipping_email,
       task_cancellation_email
)
from datetime import datetime
from django.core.cache import cache
import logging

logger = logging.getLogger('orders')



def process_checkout(user,address_id):
       lock_key = f"checkout_lock_{user.id}"
       if not cache.add(lock_key,"locked",timeout=15):
              raise ValueError("Checkout already in progress. Please wait.")
       try:
              with transaction.atomic():
                     #Get the cart
                     order = Order.objects.current_cart(user).get()
                     # Get the Address
                     address = ShippingAddress.objects.get(id = address_id, user = user)
                     product_ids = order.items.values_list('product_id',flat = True) # this line just grabs a list of the pure Database IDs for every product sitting in the user's cart (e.g., [15, 6, 42]).
                     items = order.items.all()
                     
                     for item in items:
                            product_data = get_product_details(item.product_id)
                            item.price_at_purchase = product_data['price']
                            item.save()


                     order.shipping_address = address
                     order.status = 'Pending'
                     order.save()
                     logger.info(f"Order {order.order_id} successfully processed for user {user.id}")
                    
              # EDA: Out Box publisher ---
              # Instead of synchronously calling the product.services to decut inventory (which can carsh),
              # Saving an event tot the outbox . The Background worker will pic k this up.

                     OrderEventOutbox.objects.create(
                            event_type = 'order.placed',
                            payload = {
                                   "order_id": str(order.order_id),
                                   "user_id": user.id,
                                   "items": [
                                          {"product_id":item.product_id,"quantity": item.quantity} for item in items
                                   ]
                            }
                     )

                     transaction.on_commit(lambda:task_send_payment_success_email.delay(order.order_id)) # using on_commit will stop the task to send to celery until db transaction is full commited

              return order
       finally:
              cache.delete(lock_key)

def add_to_cart_process(user,product_id,quantity):
       with transaction.atomic():
              order, order_created = Order.objects.get_or_create_cart(user)

              product_details = get_product_details(product_id)

              item, itme_created = OrderItem.objects.get_or_create(
                     order = order,
                     product_id = product_id,
                     defaults = {
                            'product_name': product_details['name']
                     }
              )

              if not  itme_created:
                     item.quantity += quantity
              else:
                     item.quantity = quantity
              item.save()

              order.save()

              return order,item
              
def update_quantity_process(user,product_id,quantity):
       with transaction.atomic():
              order = Order.objects.current_cart(user).get()
              item = OrderItem.objects.get(order=order, product_id = product_id)

              if quantity < 1:     
                     item.delete()
              else:
                     item.quantity = quantity
                     item.save()
              order.save()

              return order, item

def remove_item_process(user,product_id):
       with transaction.atomic():
              order = Order.objects.current_cart(user).get()
              item = OrderItem.objects.get(order=order, product_id= product_id)
              item.delete()
              order.save()

              return order

def update_status_process(order,new_status):

       order.status = new_status
       order.save()
              
       if new_status == "Shipped":
             task_send_shipping_email.delay(order.order_id)
       return order

def cancel_order_process(order):
       
              with transaction.atomic():
                     #Resotre Stock
                     items = order.items.all()
                     
                     items_data = [{"product_id":item.product_id, "quantity": item.quantity} for item in items]

                     OrderEventOutbox.objects.create(
                            event_type = 'order.cancelled',
                            payload = {
                                   "order_id": str(order.order_id),
                                   "items": [
                                          {"product_id":item.product_id,"quantity": item.quantity} for item in items
                                   ]
                            }
                     )

                     order.status = 'Cancelled'
                     order.save()
                     logger.info(f"Order {order.order_id} was cancelled successfully. Stock restored.")

                     transaction.on_commit(lambda: task_cancellation_email.delay(order.order_id))


              return order

def mark_as_paid_process(order):

       with transaction.atomic():
              order.is_paid= True
              order.paid_at = datetime.now()
              order.save()

              logger.info(f"Admin marked Order {order.order_id} as paid manually.")

              #Trigger Eamil: Payment Success

              transaction.on_commit(lambda:task_send_payment_success_email.delay(order.order_id))

              items = order.items.all()
              OrderEventOutbox.objects.create(
                     event_type = 'order.completed',
                     payload = {
                            "user_id": order.user_id,
                            "items": [{"product_id": item.product_id} for item in items]
                     }
              )

              return order

def has_user_purchased_product(user_id,product_id):

       return OrderItem.objects.filter(
              order__user_id = user_id,
              product_id = product_id
       ).exists()