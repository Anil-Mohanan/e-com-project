from celery import shared_task
from celery import current_app
from .emails import(
       send_order_confirmation_email,
       send_cancellation_email,
       send_shipping_email,
       send_payment_success_email,
)
from django.utils import timezone
from datetime import timedelta
from orders.services import cancel_order_process ,confirm_order_payment
from orders import repositories as default_repo
import logging 
logger = logging.getLogger(__name__)

@shared_task(bind = True, max_retries = 3)
def task_send_order_confirmation_email(self,order_id,repo=default_repo):

       try:
              email_data = repo.get_order_email_data(order_id)
              send_order_confirmation_email(email_data)
              return "Send Orders Confirmation Email is Successfull"
       except Exception as exc:
              logger.error(f"Faild to send confirmation email for {order_id} : {exc}")
              raise self.retry(exc = exc, countdown = 60)
@shared_task(bind = True, max_retries = 3)
def task_cancellation_email(self,order_id,repo=default_repo):

       try:
              email_data = repo.get_order_email_data(order_id)
              send_cancellation_email(email_data)
              return 'Send Order Cancellation Email is Successfull'
       except Exception as exc:
              logger.error(f"Failed to send Cancellation email for {order_id} : {exc}")
              raise self.retry(exc = exc, countdown = 60)
@shared_task(bind = True, max_retries = 3)
def task_send_shipping_email(self,order_id,repo=default_repo):

       try:
              email_data = repo.get_order_email_data(order_id)
              send_shipping_email(email_data)
              return 'Send Order Shipping Email is Successfull'
       except Exception as exc:
              logger.error(f"Failed to send Shipping email for {order_id} : {exc}")
              raise self.retry(exc = exc, countdown = 60)
              
@shared_task(bind = True, max_retries = 3)
def task_send_payment_success_email(self,order_id,repo=default_repo):

       try:
              email_data = repo.get_order_email_data(order_id)
              send_payment_success_email(email_data)
              return 'Send Order Payment Email is Successfull'
       except Exception as exc:
              logger.error(f"Failed to send Payment success email for {order_id} : {exc}")
              raise self.retry(exc = exc, countdown = 60)

@shared_task
def task_release_unpaid_orders(repo=default_repo):
       cutoff_time = timezone.now() - timedelta(minutes=15)
       orders = repo.get_unpaid_pending_orders(cutoff_time)
       for order_entity in orders:
              cancel_order_process(order_entity.order_id,repo = repo)

@shared_task
def sweep_order_outbox(repo=default_repo):
       events = repo.get_unprocessed_outbox_events()

       for event in events:
              try:
                     if event.event_type == 'order.placed':
                            current_app.send_task('product.handle_order_placed',args=[event.payload])
                     elif event.event_type == 'order.completed':
                                   current_app.send_task('product.handle_order_completed',args=[event.payload])
                                   task_send_payment_success_email.delay(event.payload.get('order_id'))
                     elif event.event_type == 'order.cancelled':
                            current_app.send_task('product.handle_order_cancelled',args = [event.payload])

                     repo.mark_outbox_event_processed(event.id)
                     logger.info(f"Successfully broadcasted event: {event.event_type}")
              except Exception as e:
                     repo.mark_outbox_event_failed(event.id,e)
              
                     logger.error(f"Faliled to broadcast event {event.id} : {e}")


@shared_task(name='orders.handle_inventory_failed')
def handle_inventory_failed(payload,repo=default_repo):
       order_id = payload.get("order_id")
       reason = payload.get("reason")
       
       try:
              order_entity = repo.get_order_by_id(order_id)

              if order_entity.status == "Pending":
                     logger.warning(f"SAGA Rollback: Cancelling Order {order_id} becasue Inventory Faild. Reason: {reason}") 
                     cancel_order_process(order_id,repo = repo)

       except ValueError:
              logger.error(f"SAGA Rollback Failed: Could not find order {order_id}")              


@shared_task(name = 'orders.handle_payment_successful')
def handle_payment_confirm(payload,repo=default_repo):
       
       order_id = payload.get("order_id")
       
       try:
              confirm_order_payment(order_id,repo = repo)
              logger.warning(f"Payment logic executed for Order {order_id}")
       except ValueError as e:
              logger.warning(f"Could not confirm payment for {order_id}: {e}")

