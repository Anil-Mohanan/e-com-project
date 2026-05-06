from celery import shared_task
from celery import current_app
from product.repositories import core  as default_repo
from product.services import rebuild_search_index ,deduct_inventory_for_order ,restore_inventory_for_order
import logging

logger = logging.getLogger(__name__)

# The __name__ arugument is the chanel 


# for to deduct product from inventory 
@shared_task(name="product.handle_order_placed")
def handle_order_placed_event(payload):
       items_data = payload.get('items',[])
       order_id = payload.get('order_id',None)

       try:
              deduct_inventory_for_order(items_data,order_id)
              logger.info(f"Inventory successfully deudcted for Order {order_id}")
       
       except ValueError as e:
              logger.error(f"falide to deduct inventory for Order {order_id}: {e}")

              current_app.send_task(
                     'orders.handle_inventory_failed',
                     args = [{"order_id": order_id, "reason": str(e)}]
              )

@shared_task(name = "product.handle_order_completed")
def handle_order_completed_event(payload,repo = default_repo): #product/views.py and look at your add_review endpoint.
       user_id = payload.get('user_id')
       items_data = payload.get('items',[])

       for item in items_data:
              try:
                     repo.record_product_purchase(user_id,item['product_id'])

              except Exception as e:
                     logger.error(f"CQRS faild to record purchase for user {user_id} : {e}")

@shared_task(name="product.handle_order_cancelled")
def handle_order_cancelle_event(payload):
       items_data = payload.get('items',[])
       order_id = payload.get('order_id',None)

       restore_inventory_for_order(items_data,order_id)

@shared_task
def task_rebuild_search_index(repo = default_repo):
       rebuild_search_index(repo)


@shared_task(name = "product.compute_recommendations")
def task_compute_recommendations():
       """
       Nightly task: reads ProductBehaviorLog co-view data and Writes
       pre-computed results to ProductRecommendationtable .
       
       """
       from product.repositories import core as repo
       # Local import inside the task body - avoid circular import at startup

       logger.info('Starting nightly recommendation computation....')

       all_product_ids = repo.get_all_product_ids()
       # Compute recommendation for every active product


       compouted_count = 0

       for product_id in all_product_ids:
              raw_recs = repo.get_frequently_viewed_together(
                     product_id = product_id,
                     days = 30,# look back 30 days of behaviro data for the signal
                     limit = 10, # compoute the top 10 cnadiate - The Api will trim to 5
              )

              

              if raw_recs:
                     
                     #Normalize: get_frequently_viewed_together retuns co_view_count
                     #save_recommendations a 'score' key.
                     #rename co_view_count -> score here so the repo layer stays clean

                     normalized = [
                            {
                                   'product_id': rec['product_id'],# The co-viewed product
                                   'score':float(rec['co_view_count'])# <- renaming the field 
                            }
                            for rec in raw_recs
                     ]
                     repo.save_recommendations(product_id,normalized)# writes to productRecommendation table using update_or_crate
                     compouted_count += 1

       logger.info(f"Recommendation computation complete. {compouted_count} product updated.")

@shared_task(name="product.sync_product_embedding",bind=True, max_retries = 3)
def task_sync_product_embedding(self, product_id: int, name: str, brand: str, description: str):

       # max_retries=3 — if HuggingFace or Pinecone is temporarily down, Celery will retry 3 times before giving up

       from product.services.vector_search import upsert_product_embedding
       # only loads when this specific task is actually runs

       try:
              upsert_product_embedding(
                     product_id = product_id,
                     name = name,
                     brand= brand or "", 
                     description= description or "", 
              )
              #brand or "" - product.brand is nullable in model(null = True , blank = True)
              # If brand is none passing empty string 
       
       except Exception as exc:
              logger.error(
                     f"Embedding sync failed for product_ids = {product_id}, retrying.... Error : {exc}"

              )
              raise self.retry(exc = exc, countdown = 60)
              # self.retry() tells celery: "this failed , wait 60 sec and try again"
              # After max_retries=3 attempts, Celery marks the task as FAILED and stops
              # We raise it (not just call it) because retry() raises a special Celery exception internally
