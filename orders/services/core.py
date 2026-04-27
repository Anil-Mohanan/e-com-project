from orders.repositories import core as default_repo
from product.services import get_product_details, get_product_price
from orders.infrastructure.tasks import (
       task_send_payment_success_email,
       task_send_order_confirmation_email,
       task_send_shipping_email,
       task_cancellation_email
)
from django.core.cache import cache
import logging

logger = logging.getLogger('orders')



def process_checkout(user,address_id,repo=default_repo):

       lock_key = f"checkout_lock_{user.id}"
       if not cache.add(lock_key,"locked",timeout=15):
              raise ValueError("Checkout already in progress. Please wait.")
       
       try:
              existing =  repo.get_pending_order_for_user(user.id)
              if existing:
                     return existing

              
              #Get the cart
              cart_entity = repo.get_cart(user)
                    
              for item in cart_entity.items:
                            
                     live_price = get_product_price(item.product_id,variant_id=item.variant_id)

                     repo.set_item_price(cart_entity.order_id, item.product_id,live_price)


              repo.checkout_order(cart_entity.order_id, address_id, user)       
              logger.info(f"Order {cart_entity.order_id} successfully processed for user {user.id}")
                    
              # EDA: Out Box publisher ---
              # Instead of synchronously calling the product.services to decut inventory (which can carsh),
              # Saving an event tot the outbox . The Background worker will pic k this up.

              items_data = repo.get_order_items_data(cart_entity.order_id)

              payload = {
                     'order_id' : cart_entity.order_id,
                     'items' : items_data
              }

              repo.create_outbox_event('order.placed',payload)

              
              task_send_order_confirmation_email.delay(cart_entity.order_id)

              return repo.get_order_by_id(cart_entity.order_id)

       finally:
              cache.delete(lock_key)

def get_user_cart(user,repo = default_repo):
       cart, created = repo.get_or_create_cart(user)
       return cart

def add_to_cart_process(user, product_id, quantity,repo=default_repo):
    cart, created = repo.get_or_create_cart(user)

    product_details = get_product_details(product_id)

    repo.add_item_to_cart(cart.order_id, product_id, product_details['name'], quantity)

    return repo.get_cart(user)

              
def update_quantity_process(user,product_id,quantity,repo=default_repo):
              cart = repo.get_cart(user)

              item = repo.update_item_quantity(cart.order_id,product_id,quantity)

              return repo.get_cart(user), item

def remove_item_process(user,product_id,repo=default_repo):
              cart_entity =  repo.get_cart(user)
              order = repo.delete_item(cart_entity.order_id, product_id)

              return order

def update_status_process(order_id,new_status,repo=default_repo):

       repo.save_order_status(order_id, new_status)
              
       if new_status == "Shipped":
             task_send_shipping_email.delay(order_id)

       return repo.get_order_by_id(order_id)

def cancel_order_process(order_id,repo=default_repo):

       order_entity = repo.get_order_by_id(order_id)


       if order_entity.status == 'Cancelled':
              return order_entity

       
              #Resotre Stock
       items_data = repo.get_order_items_data(order_id)
              
       repo.save_order_status(order_id, 'Cancelled')
       
       payload = {
              "order_id": order_entity.order_id,
              "items" : items_data
       }

       repo.create_outbox_event('order.cancelled',payload)
       
       logger.info(f"Order {order_entity.order_id} was cancelled successfully. Stock restored.")
       task_cancellation_email.delay(order_entity.order_id)

       return repo.get_order_by_id(order_id)

def mark_as_paid_process(order_id,repo=default_repo):
       order_entity = repo.get_order_by_id(order_id)
       if order_entity.is_paid:
              return order_entity

       repo.mark_order_paid(order_id)

       logger.info(f"Admin marked Order {order_entity.order_id} as paid manually.")

       #Trigger Eamil: Payment Success

       task_send_payment_success_email.delay(order_entity.order_id)

       items_data = repo.get_order_items_data(order_id)

       payload = {
              "order_id": order_entity.order_id,
              "items" : items_data
       }

       repo.create_outbox_event('order.completed',payload)
       
       return repo.get_order_by_id(order_id)

def sync_order_prices(order_id,repo=default_repo):

       """
       Bridge Service: Fetches live prices from the Product app and updates 
       the Cart items so that the Order model's total_price is accurate.
       """
       order_entity = repo.get_order_by_id(order_id)

       if order_entity.status != 'Cart':
              return
       
       for item in order_entity.items:

              live_price = get_product_price(item.product_id,variant_id=item.variant_id)

              repo.set_item_price(order_id, item.product_id,live_price)

       logger.info(f'Price synced for Cart {order_entity.order_id}')