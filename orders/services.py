from .models import ShippingAddress, Order, OrderItem
from product.models import Product , ProductVariant, Category, InventoryUnit
from django.db import transaction
from .tasks import (
       task_send_payment_success_email,
       task_send_order_confirmation_email,
       task_send_shipping_email,
       task_cancellation_email
)
from datetime import datetime
import logging

logger = logging.getLogger('orders')

def process_checkout(user,address_id):
       with transaction.atomic():
              #Get the cart
              order = Order.objects.current_cart(user).get()
              # Get the Address
              address = ShippingAddress.objects.get(id = address_id, user = user)
              product_ids = order.items.values_list('product_id',flat = True) # this line just grabs a list of the pure Database IDs for every product sitting in the user's cart (e.g., [15, 6, 42]).
              products = Product.objects.select_for_update().filter(id__in = product_ids).order_by('id')#.filter(id__in=product_ids) tells the database to get only the products in the cart.
              locked_products_dict = {p.id: p for p in products}
              
              items = order.items.all()
              
              for item in items:
                     product = locked_products_dict[item.product_id]
                     available_units = list(InventoryUnit.objects.select_for_update().filter(product=product,status="In Stock")[:item.quantity]) # 1. Going into the warehouse to look for physical boxes
                     if len(available_units) < item.quantity:
                            raise ValueError(f"Sorry, {product.name} is out of stock. (Database mismatch: missing physical inventory units).")
                     for unit in available_units:
                            unit.status = 'Sold'

                     InventoryUnit.objects.bulk_update(available_units,['status'])
                     item.inventory_units.set(avalible_units)
                     product.stock -= item.quantity
                     product.save()
                     item.price_at_purchase = product.price # Saving the price now so if the changes later , the order history is correct
                     
                     item.save()
                     
              order.shipping_address = address
              order.status = 'Pending'
              order.save()
              logger.info(f"Order {order.order_id} successfully processed for user {user.id}")

              transaction.on_commit(lambda:task_send_payment_success_email.delay(order.order_id)) # using on_commit will stop the task to send to celery until db transaction is full commited
              
       return order

def add_to_cart_process(user,product_id,quantity):
       with transaction.atomic():
              order, order_created = Order.objects.get_or_create_cart(user)

              item, itme_created = OrderItem.objects.get_or_create(
                     order = order,
                     product_id = product_id
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
                     product_ids = order.items.values_list('product_id',flat = True)
                     products = Product.objects.select_for_update().filter(id__in = product_ids).order_by('id')
                     locked_products_dict = {p.id : p for p in products}
                     items = order.items.all() # items is related name in models.py OrderItem model
                     for item in items:
                            product = locked_products_dict[item.product_id]
                            product.stock += item.quantity# Add it back!
                            product.save()
                     order.status = 'Cancelled'
                     order.save()
                     logger.info(f"Order {order.order_id} was cancelled successfully. Stock restored.")

                     transaction.on_commit(lambda: task_cancellation_email.delay(order.order_id))


              return order

def mark_as_paid_process(order):
       order.is_paid= True
       order.paid_at = datetime.now()
       order.save()

       logger.info(f"Admin marked Order {order.order_id} as paid manually.")
       
       #Trigger Eamil: Payment Success
       
       task_send_payment_success_email.delay(order.order_id)

       return order