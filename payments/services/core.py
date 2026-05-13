import stripe # The official library provided by Stripe to talk to their servers
from django.conf import settings # to access the keys in settings.py
import logging
from decimal import Decimal
from payments.repositories import core as default_repo
from payments.domain import StripePaymentStrategy

logger = logging.getLogger(__name__)

PAYMENT_STRATEGIES = {
       'stripe': StripePaymentStrategy(),
}

def create_checkout_session(user,order_id,gateway = 'stripe', repo = default_repo):
       """
       Now this function does not know about stripe. It just ask the dictionary for the right strategy.(DEPENDENCY INVERSION!)
       """
       from orders.services import get_order_details_for_payment 
       order_data = get_order_details_for_payment(order_id,user)

       if repo.has_successful_payment(order_id):
              raise ValueError("This order is already Paid")
       strategy = PAYMENT_STRATEGIES.get(gateway.lower())

       if not strategy:
              raise ValueError(f'Unsupported payment gateway: {gateway}')

       return strategy.create_checkout(user,order_data,repo)

def handle_stripe_event(event, repo=default_repo):
       """SRP: This function ONLY routes events."""
       event_type = event.get('type')
       intent = event['data']['object']
       
       if event_type == 'payment_intent.succeeded':
              _handle_success(intent, repo)
       elif event_type == 'payment_intent.processing':
              _handle_processing(intent, repo)
       elif event_type == 'payment_intent.payment_failed':
              _handle_failure(intent, repo)

def _handle_success(intent, repo):
       """SRP: This function ONLY handles successful payments."""
       transaction_id = intent['id']
       order_id = intent['metadata'].get('order_id')
       
       try:
              was_updated = repo.update_payment_status(transaction_id, "Success")
              if not was_updated:
                     return
              payload = {"order_id": str(order_id)}
              repo.create_outbox_event('payment.successful', payload)
       except ValueError:
              logger.warning(f"Payment record missing for transaction {transaction_id}, but stripe succeeded")
              amount = Decimal(intent['amount']) / Decimal('100')
              repo.create_payment(order_id, 'Success', 'Stripe', transaction_id, amount)
              
              payload = {"order_id": str(order_id)}
              repo.create_outbox_event('payment.successful', payload)
       except Exception as e:
              logger.error(f"Unexpected error in payment webhook [{type(e).__name__}]: {e}")

def _handle_processing(intent, repo):
       """SRP: This function ONLY handles processing state."""
       transaction_id = intent['id']
       try:
              repo.update_payment_status(transaction_id, 'Processing')
       except ValueError:
              logger.error(f"Webhook received failure for unknown Transaction {transaction_id}")
       except Exception as e:
              logger.error(f"Unexpected DB error in Webhook processing case: {e}")

def _handle_failure(intent, repo):
       """SRP: This function ONLY handles declined cards."""
       transaction_id = intent['id']
       error_message = intent.get('last_payment_error', {}).get('message', 'Unknown error')
       
       try:
              repo.update_payment_status(transaction_id, "Failed")
              logger.warning(f"Payment Failed for Transaction {transaction_id}: {error_message}")
       except ValueError:
              logger.error(f"Webhook received failure for unknown Transaction {transaction_id}")
       except Exception as e:
              logger.error(f"Unexpected DB error in Webhook failure case: {e}")