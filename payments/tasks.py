from celery import shared_task
from celery import current_app 
from django.utils import timezone
from .services import handle_stripe_event
from .models import PaymentEventOutbox
import logging

logger = logging.getLogger(__name__)

@shared_task(bind= True, max_retries = 3)
def process_stripe_webhook_task(self,event_data):
       """Take the raw webhook data from strie and process the database changes"""

       logger.info("Processing Stripe webhook in background.....")

       try:
              handle_stripe_event(event_data)
              return  'webhook process successfully'
       except Exception as exc:
              logger.error(f"webhook processing failed. Retrying... ")
              raise self.retry(exc = exc, countdown = 30)
              

@shared_task
def sweeper_payment_outbox():
       events = PaymentEventOutbox.objects.filter(processed = False, retry_count__lt = 5).order_by('created_at')

       for event in events:
              try:
                     if event.event_type == 'payment.successful':
                            current_app.send_task('orders.handle_payment_successful',args = [event.payload])
                     event.processed = True
                     event.processed_at = timezone.now()
                     event.save()
                     logger.info(f"Successfully broadcasted event: {event.event_type}")
              except Exception as e:
                     event.error_message = str(e)
                     event.retry_count += 1
                     event.save()
                     logger.error(f"Faliled to broadcast event {event.id} : {e}")


       