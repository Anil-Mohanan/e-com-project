from celery import shared_task
from celery import current_app
from .services import deduct_inventory_for_order,restore_inventory_for_order
from .models import ProductPurchaseHistory
import logging

logger = logging.getLogger(__name__)

# The __name__ arugument is the chanel 


# for to deduct product from inventory 
@shared_task(name="product.handle_order_placed")
def handle_order_placed_event(payload):
       items_data = payload.get('items',[])
       order_id = payload.get('order_id')

       try:
              deduct_inventory_for_order(items_data)
              logger.info(f"Inventory successfully deudcted for Order {order_id}")
       
       except ValueError as e:
              logger.error(f"falide to deduct inventory for Order {order_id}: {e}")

              current_app.send_task(
                     'orders.handle_inventory_failed',
                     args = [{"order_id": order_id, "reason": str(e)}]
              )

@shared_task(name = "product.handle_order_completed")
def handle_order_completed_event(payload): #product/views.py and look at your add_review endpoint.
       user_id = payload.get('user_id')
       items_data = payload.get('items',[])

       for item in items_data:
              try:
                     ProductPurchaseHistory.objects.get_or_create(
                            user_id = user_id,
                            product_id = item['product_id']
                     )
              except Exception as e:
                     logger.error(f"CQRS faild to record purchase for user {user_id} : {e}")

@shared_task(name="product.handle_order_cancelled")
def handle_order_cancelle_event(payload):
       items_data = payload.get('items',[])

       restore_inventory_for_order(items_data)