import pytest
import uuid
from payments.models import Payment, PaymentEventOutbox
from django.db import IntegrityError

# @pytest.mark.django_db tells Pytest this function needs access to the live Test Database
@pytest.mark.django_db
def test_payment_creation():
       # 1: SETUP: Create a raw UUID for the decoupled Order id
       fake_order_id = uuid.uuid4()

       #2. Act: Create a payment manually
       payment = Payment.objects.create(
              order_id = fake_order_id,
              transaction_id = 'txn_strip_12345',
              payment_method = "Stripe",
              amount = 1500.50
       )

       assert payment.status == "Pending"
       assert payment.payment_method == "Stripe"
       assert str(payment) == "Stripe - 1500.5 - Pending"

@pytest.mark.django_db
def test_payment_outbox_event_creation():
    # 1. ACT
    outbox_event = PaymentEventOutbox.objects.create(
        event_type="payment.success",
        payload={"order_id": str(uuid.uuid4()), "amount": 1500.50}
    )
    
    # 2. ASSERT: A new outbox event should always start unprocessed with zero retries.
    assert outbox_event.processed is False
    assert outbox_event.retry_count == 0
    assert "payment.success" in outbox_event.event_type

@pytest.mark.django_db
def test_payment_order_id_must_be_unique():
        # 1. SETUP: Create one Order ID
       shared_order_id = uuid.uuid4()
       
       # 2. Give the order its first successful payment
       Payment.objects.create(
              order_id=shared_order_id,
              transaction_id="txn_first_payment",
              payment_method="Stripe",
              amount=100.00
       )
       
       # 3. ACT & ASSERT: A second payment for the same order MUST trigger a hard Database Crash!
       # Pytest will look for the IntegrityError. If the DB doesn't crash, the test FAILS!
       with pytest.raises(IntegrityError):
              Payment.objects.create(
                     order_id=shared_order_id, # Using the exact same order_id!
                     transaction_id="txn_second_payment",
                     payment_method="Stripe",
                     amount=50.00
              )