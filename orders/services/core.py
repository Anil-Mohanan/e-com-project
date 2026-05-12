from math import exp
from orders.repositories import core as default_repo
from product.services import get_product_details, get_product_price
from orders.events import (
    order_event_bus,
    OrderPlaced,
    OrderCancelled,
    OrderPaid,
    OrderShipped,
)
from product.events import product_event_bus, ProductAddedToCart
# ↑ This is cross-domain publishing — the ORDERS service fires a PRODUCT event.
# This is valid. The orders service OWNS the cart action (it's the publisher).
# The product domain OWNS the reaction (it's the subscriber/handler).
from analytics.services import record_admin_action
from django.db import transaction
from django.core.cache import cache
import logging

logger = logging.getLogger('orders')



def process_checkout(user,address_id,product_ids=None,repo=default_repo):

       lock_key = f"checkout_lock_{user.id}"
       if not cache.add(lock_key,"locked",timeout=15):
              raise ValueError("Checkout already in progress. Please wait.")
       
       try:   
              with transaction.atomic():
                     # existing =  repo.get_pending_order_for_user(user.id)
                     # if existing and not product_ids:
                     #        return existing

                     #Get the cart
                     cart_entity = repo.get_cart(user)

                     if not cart_entity.items:
                            raise ValueError("Cannot checkout with an empty cart.")

                     for item in cart_entity.items:

                            live_price = get_product_price(item.product_id,variant_id=item.variant_id)

                            repo.set_item_price(cart_entity.order_id, item.product_id,live_price)

                     # SELECTIVE CHECKOUT: If product_ids provided, split the cart

                     if product_ids:
                            order_entity = repo.split_and_checkout(cart_entity.order_id, product_ids, address_id, user)
                     else:
                            repo.checkout_order(cart_entity.order_id, address_id, user)
                            order_entity = repo.get_order_by_id(cart_entity.order_id)
                     repo.record_order_event(
                            order_id = cart_entity.order_id,# the UUID from the entity
                            event_type = 'order.placed',# the immutable fact name
                            actor_id = user.id,
                            actor_type = 'user',
                            payload = {
                                   "previous_status": "Cart",
                                   "new_status": "Pending",
                                   "total": str(order_entity.total_price),
                            }
                     )   
                     logger.info(f"Order {cart_entity.order_id} successfully processed for user {user.id}")

                     # EDA: Out Box publisher ---
                     # Instead of synchronously calling the product.services to decut inventory (which can carsh),
                     # Saving an event tot the outbox . The Background worker will pic k this up.

                     items_data = repo.get_order_items_data(order_entity.order_id)

                     payload = {
                            'order_id' : order_entity.order_id,
                            'items' : items_data,
                            'user_id' : user.id
                     }

                     order_event_bus.publish(OrderPlaced(payload=payload))

                     return order_entity              
       except Exception as e:
              logger.error(f"Checkout failed for user {user.id}: {e}")

              raise e
              
       finally:
              cache.delete(lock_key)

def get_user_cart(user,repo = default_repo):
       cart, created = repo.get_or_create_cart(user)
       return cart

def add_to_cart_process(user, product_id, quantity,repo=default_repo):
    cart, created = repo.get_or_create_cart(user)

    product_details = get_product_details(product_id)

    repo.add_item_to_cart(cart.order_id, product_id, product_details['name'], quantity)

    product_event_bus.publish(ProductAddedToCart(
       payload={
              "product_id": product_id,
              "user_id": user.id,
              "quantity": quantity,
       }
    ))

    return repo.get_cart(user)
              
def update_quantity_process(user,product_id,quantity,repo=default_repo):
              cart = repo.get_cart(user)

              item = repo.update_item_quantity(cart.order_id,product_id,quantity)

              return repo.get_cart(user), item

def remove_item_process(user,product_id,repo=default_repo):
              cart_entity =  repo.get_cart(user)
              order = repo.delete_item(cart_entity.order_id, product_id)

              return order

def update_status_process(order_id,new_status,actor = None,repo=default_repo):

       order_entity = repo.get_order_by_id(order_id)
       
       repo.save_order_status(order_id, new_status)

       record_admin_action(
              actor_id=getattr(actor, 'id', None),
              actor_email = getattr(actor, 'email', 'system'),
              action = 'order.status_changed',
              target_id = order_id,
              old_value = {'status': order_entity.status},
              new_value = {'status': new_status},
       )
              
       if new_status == "Shipped":
             payload = {"order_id": order_id}
             order_event_bus.publish(OrderShipped(payload= payload))


       return repo.get_order_by_id(order_id)

def cancel_order_process(order_id,repo=default_repo):

       order_entity = repo.get_order_by_id(order_id)

       if order_entity.status == 'Cancelled':
              return order_entity

       if order_entity.status not in ["Pending", "Paid"]:
              raise  ValueError("Order cannot be cancelled in its current state")

       
              #Resotre Stock
       items_data = repo.get_order_items_data(order_id)
              
       repo.save_order_status(order_id, 'Cancelled')
       
       payload = {
              "order_id": order_entity.order_id,
              "items" : items_data,
              "user_id": order_entity.user_id
       }

       
       
       logger.info(f"Order {order_entity.order_id} was cancelled successfully. Stock restored.")
       order_event_bus.publish(OrderCancelled(payload = payload))


       return repo.get_order_by_id(order_id)

def mark_as_paid_process(order_id,repo=default_repo):
       order_entity = repo.get_order_by_id(order_id)
       if order_entity.is_paid:
              return order_entity

       repo.mark_order_paid(order_id)

       logger.info(f"Admin marked Order {order_entity.order_id} as paid manually.")

       

       items_data = repo.get_order_items_data(order_id)

       payload = {
              "order_id": order_entity.order_id,
              "items" : items_data,
              "user_id": order_entity.user_id
       }

       order_event_bus.publish(OrderPaid(payload = payload))
       
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