from celery import shared_task
from .models import Order
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

