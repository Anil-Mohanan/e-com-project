from celery import shared_task
from celery import current_app 
from .services import handle_stripe_event
from . import repositories as default_repo
import logging

logger = logging.getLogger(__name__)

@shared_task(bind= True, max_retries = 3)
def process_stripe_webhook_task(self,event_data,repo=default_repo):
       """Take the raw webhook data from strie and process the database changes"""

       logger.info("Processing Stripe webhook in background.....")

       try:
              handle_stripe_event(event_data,repo)
              return  'webhook process successfully'
       except Exception as exc:
              logger.error(f"webhook processing failed. Retrying... ")
              raise self.retry(exc = exc, countdown = 30)
              

@shared_task
def sweeper_payment_outbox(repo=default_repo):
       events = repo.get_unprocessed_outbox_events()

       for event in events:
              try:
                     if event.event_type == 'payment.successful':
                            current_app.send_task('orders.handle_payment_successful',args = [event.payload])
                     repo.mark_out_box_event_processed(event.id)
                     logger.info(f"Successfully broadcasted event: {event.event_type}")
              except Exception as e:
                     repo.mark_outbox_event_failed(event.id,e)
                     logger.error(f"Faliled to broadcast event {event.id} : {e}")

