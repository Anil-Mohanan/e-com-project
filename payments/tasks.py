from celery import shared_task
from .services import handle_stripe_event
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
              