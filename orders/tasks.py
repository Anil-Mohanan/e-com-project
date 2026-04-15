from celery import shared_task
from .models import Order , OrderEventOutbox
from celery import current_app
from .emails import(
       send_order_confirmation_email,
       send_cancellation_email,
       send_shipping_email,
       send_payment_success_email,
)
from django.utils import timezone
from datetime import timedelta
import logging 
logger = logging.getLogger(__name__)

@shared_task(bind = True, max_retries = 3)
def task_send_order_confirmation_email(self,order_id):

       try:
              order = Order.objects.get(order_id = order_id)
              send_order_confirmation_email(order)
              return "Send Orders Confirmation Email is Successfull"
       except Exception as exc:
              logger.error(f"Faild to send confirmation email for {order_id} : {exc}")
              raise self.retry(exc = exc, countdown = 60)
@shared_task(bind = True, max_retries = 3)
def task_cancellation_email(self,order_id):

       try:
              order  = Order.objects.get(order_id = order_id)
              send_cancellation_email(order)
              return 'Send Order Cancellation Email is Successfull'
       except Exception as exc:
              logger.error(f"Failed to send Cancellation email for {order_id} : {exc}")
              raise self.retry(exc = exc, countdown = 60)
@shared_task(bind = True, max_retries = 3)
def task_send_shipping_email(self,order_id):

       try:
              order  = Order.objects.get(order_id = order_id)
              send_shipping_email(order)
              return 'Send Order Shipping Email is Successfull'
       except Exception as exc:
              logger.error(f"Failed to send Shipping email for {order_id} : {exc}")
              raise self.retry(exc = exc, countdown = 60)
              
@shared_task(bind = True, max_retries = 3)
def task_send_payment_success_email(self,order_id):

       try:
              order  = Order.objects.get(order_id = order_id)
              send_payment_success_email(order)
              return 'Send Order Payment Email is Successfull'
       except Exception as exc:
              logger.error(f"Failed to send Payment success email for {order_id} : {exc}")
              raise self.retry(exc = exc, countdown = 60)

@shared_task
def task_release_unpaid_orders():
       from .services import cancel_order_process
       cutoff_time = timezone.now() - timedelta(minutes=15)
       orders = Order.objects.filter(status = 'Pending', created_at__lte = cutoff_time)
       for order in orders:
              cancel_order_process(order)

@shared_task
def sweep_order_outbox():
       events = OrderEventOutbox.objects.filter(processed = False, retry_count__lt = 5).order_by('created_at')

       for event in events:
              try:
                     if event.event_type == 'order.placed':
                            current_app.send_task('product.handle_order_placed',args=[event.payload])
                     elif event.event_type == 'order.completed':
                                   current_app.send_task('product.handle_order_completed',args=[event.payload])
                     elif event.event_type == 'order.cancelled':
                            current_app.send_task('product.handle_order_cancelled',args = [event.payload])

                     event.processed = True
                     event.processed_at = timezone.now()
                     event.save()
                     logger.info(f"Successfully broadcasted event: {event.event_type}")
              except Exception as e:
                     event.error_message = str(e)
                     event.retry_count += 1
                     if event.retry_count == 5:
                            logger.critical(f"Failed to Excecte even {event.id}")
                     event.save()
                     logger.error(f"Faliled to broadcast event {event.id} : {e}")


@shared_task(name='orders.handle_inventory_failed')
def handle_inventory_failed(payload):
       order_id = payload.get("order_id")
       reason = payload.get("reason")
       
       try:
              order = Order.objects.get(order_id= order_id)

              if order.status == "Pending":
                     logger.warning(f"SAGA Rollback: Cancelling Order {order_id} becasue Inventory Faild. Reason: {reason}") 
                     from .services import cancel_order_process
                     cancel_order_process(order)

       except Order.DoesNotExist:
              logger.error(f"SAGA Rollback Failed: Could not find order {order_id}")              


@shared_task(name = 'orders.handle_payment_successful')
def handle_payment_confirm(payload):
       
       order_id = payload.get("order_id")
       from .payment_services import confirm_order_payment
       try:
              confirm_order_payment(order_id)
              logger.warning(f"Payment logic executed for Order {order_id}")
       except ValueError as e:
              logger.warning(f"Could not confirm payment for {order_id}: {e}")

