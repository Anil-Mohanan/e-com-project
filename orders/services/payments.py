from orders.repositories import core as default_repo
from orders import domain

def get_order_details_for_payment(order_id , user,repo=default_repo):
       from .core import sync_order_prices
       sync_order_prices(order_id, repo=repo)
       
       order_entity = repo.get_order_for_user(order_id, user.id)
       
       if order_entity.is_paid:
              raise ValueError("This order  is already Paid")

       return {
              'order_id': order_entity.order_id,
              'total_price': domain.calculate_order_total(order_entity.subtotal)
       }

def confirm_order_payment(order_id,repo=default_repo):
       
       order_entity = repo.get_order_by_id(order_id)
       if order_entity.is_paid:
              return
       
       repo.mark_order_paid(order_id)

       repo.save_order_status(order_id , "OrderConfirmed")

       items_data = repo.get_order_items_data(order_id)

       payload = {
              "user_id" : order_entity.user_id,
              "items": items_data,
              "order_id": str(order_id)
       }

       repo.create_outbox_event('order.completed',payload)


