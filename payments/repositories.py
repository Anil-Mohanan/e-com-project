from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from .models import Payment, PaymentEventOutbox
from .domain import PaymentEntity , PaymentEventEntity
import logging

logger = logging.getLogger(__name__)

def _to_entity(payment):

    return PaymentEntity(
        order_id = str(payment.order_id),
        transaction_id = payment.transaction_id,
        payment_method = payment.payment_method,
        amount = payment.amount,
        status = payment.status,
        created_at = payment.created_at
    )
 
 #--------- PAYMENT READS ------------ #

def has_successful_payment(order_id) -> bool:

       has_successful_payment = Payment.objects.filter(order_id = order_id, status = "Success").exists()

       return has_successful_payment



#  -----------PAYMENT WRITES------------  #

def create_or_update_payment(order_id, defaults) -> PaymentEntity:

       payment, created = Payment.objects.update_or_create(
              order_id = order_id,
              defaults = defaults
       )

       return _to_entity(payment)

def update_payment_status(transaction_id,status):
       with transaction.atomic():
       
              try:
                     payment = Payment.objects.select_for_update().get(transaction_id = transaction_id)
                     if payment.status == status:
                            return False
                     payment.status = status 
                     payment.save()
                     return True
              except Payment.DoesNotExist:
                     raise ValueError("Payment not found for to update status")

def create_payment(order_id,status,method,tx_id,amount) -> PaymentEntity:

       payment = Payment.objects.create(
              order_id = order_id,
              status = status,
              payment_method = method,
              transaction_id = tx_id,
              amount = amount
       )
       return _to_entity(payment)

#  --------- EVENT OPERATIONS ---------  #

def create_outbox_event(event_type,payload):

       PaymentEventOutbox.objects.create(event_type = event_type,payload = payload)

def get_unprocessed_outbox_events():

       events = PaymentEventOutbox.objects.filter(processed = False, retry_count_lt = 5,).order_by('created_at')

       return [
              PaymentEventEntity(id = e.id, event_type=e.event_type,payload=e.payload) for e in events
       ]

def mark_out_box_event_processed(event_id):
       event = PaymentEventOutbox.objects.get(id = event_id)
       event.processed = True
       event.processed_at = timezone.now()
       event.save()

def mark_outbox_event_failed(event_id,error_messgae):
       event = PaymentEventOutbox.objects.get(id = event_id)
       event.error_message = str(error_messgae)
       event.retry_count += 1
       event.save()
