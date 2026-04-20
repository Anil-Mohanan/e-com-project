from billiard.sharedctypes import Value
from kombu import uuid
import pytest
import uuid
from unittest.mock import patch
from django.conf import settings
from payments.services import create_stripe_checkout , handle_stripe_event
from payments.models import Payment, PaymentEventOutbox
from user_auth.tests.factories import UserFactory

@pytest.mark.django_db
@patch('payments.services.get_order_details_for_payment')
def test_create_checkout_prevents_double_payment(mock_get_order):
       user = UserFactory()
       order_id = uuid.uuid4()
       # 1. SETUP: Create an order that is ALREADY PAID in the database
       Payment.objects.create(
              order_id = order_id,
              transaction_id = 'pi_alredy_paid',
              status = 'Success',
              payment_method = "Stripe",
              amount = 100.00
       )
       mock_get_order.return_value = {
              "order_id": order_id,
              "total_price": 100.00
       }
       with pytest.raises(ValueError,match = "This order is already paid"):
              create_stripe_checkout(user = user, order_id = order_id)

@pytest.mark.django_db
@patch('payments.services.get_order_details_for_payment')
@patch('payments.services.stripe.PaymentIntent.create')
def test_create_checkout_success(mock_stripe_create,mock_get_order):
       user = UserFactory()
       order_id = uuid.uuid4()

       mock_get_order.return_value = {
              "order_id": order_id,
              "total_price": 1500.50
       }
       # Hijack the outbound network call to Stripe
       mock_stripe_create.return_value = {
              "id": "pi_12345",
              "client_secret": "secret_abc"
       }
       # 2 ACT

       result = create_stripe_checkout(user=user, order_id=order_id)

       # 3 ASSERT: Did it return the exact secret required by React?

       assert result['client_secret'] == 'secret_abc'
       assert result['stripe_public_key'] == settings.STRIPE_PUBLIC_KEY

       # 4: ASSERT: Did it saeva Pending tracker to the database
       payment = Payment.objects.get(order_id = order_id)

       assert payment.status == 'Pending'
       assert payment.transaction_id == 'pi_12345'
       assert float(payment.amount) == 1500.50

@pytest.mark.django_db
@patch('payments.services.get_order_details_for_payment')
@patch('payments.services.stripe.PaymentIntent.create')

def test_create_checkout_updates_existing_pending_payment(mock_stripe_create,mock_get_order):

       # 1: Setup: The user clickec the "Pay" an hour ago. There is already a Pending payment in the DB.
       user = UserFactory()
       order_id = uuid.uuid4()

       Payment.objects.create(
              order_id = order_id,
              status = "Pending",
              payment_method = "Stripe",
              transaction_id = 'pi_OLD_123',
              amount = 1500.50
       )
       mock_get_order.return_value  = {
              "order_id": order_id,
              "total_price": 1500.50,
       }
       # Stripe returns a NEW transaction ID for their second attempt
       mock_stripe_create.return_value = {
              "id": "pi_NEW_999",
              "client_secret": "secret_xyz"
       }
       # 2. ACT: User clicks "Pay" a second time
       create_stripe_checkout(user=user, order_id=order_id)
       
       # 3. ASSERT: The database MUST NOT have 2 rows for this order! 
       # It must update the existing row, keeping the database perfectly clean.
       assert Payment.objects.filter(order_id=order_id).count() == 1
       
       # 4. ASSERT: The single row must be updated with the NEW transaction ID
       payment = Payment.objects.get(order_id=order_id)
       assert payment.transaction_id == "pi_NEW_999"


@pytest.mark.django_db
def test_handle_stripe_event_success():
       # 1: SETUP : we have a normal Pending payment
       order_id = uuid.uuid4()
       Payment.objects.create(
              order_id = order_id,
              transaction_id = 'pi_webhook_test',
              status = "Pending",
              amount = 100.00
       )

       # Simulate the exact dictinoar Stripe sends to our webhook
       stripe_event = {
              "type": "payment_intent.succeeded",
              "data": {
                     "object": {
                            "id" : "pi_webhook_test",
                            "amount": 10000,
                            "metadata": {"order_id": str(order_id)}
                     }      

              }
       }
       # ACT: Process the webhook event
       handle_stripe_event(stripe_event)

       # Assert the payment is upgraded to test_create_checkout_success

       payment = Payment.objects.get(transaction_id = 'pi_webhook_test')

       assert payment.status == "Success"

       # Assert The critical event outbox record was created for the asynchorouns workder 

       assert PaymentEventOutbox.objects.count() == 1

       outbox  = PaymentEventOutbox.objects.first()
       
       assert outbox.event_type == 'payment.successful'

       assert outbox.payload["order_id"] == str(order_id)

@pytest.mark.django_db
def test_handle_stripe_event_success_idempotency_prevents_triple_shipping():
       #1. Setup
       order_id = uuid.uuid4()
       Payment.objects.create(
              order_id = order_id,
              transaction_id = 'pi_glitch',
              status = "Pending",
              amount = 100.00
       )

       stripe_event = {
              "type": "payment_intent.succeeded",
              "data": {
                     "object": {
                            "id": "pi_glitch",
                            "amount": 10000,
                            "metadata": {"order_id": str(order_id)}
                     }
              }
       }
       # 2. ACT: We simulate Stripe going crazy and sending the event 3 times in a row!

       handle_stripe_event(stripe_event)
       handle_stripe_event(stripe_event)
       handle_stripe_event(stripe_event) 

       # 3. ASSERT: If your select_for_update() idempotency lock works...
       # Your system must only generate ONE shipping event, saving the company from ruin.
       assert PaymentEventOutbox.objects.count() == 1

@pytest.mark.django_db
def test_handle_stripe_event_self_heals_missing_database_record():
       # 1 Setup : Notice we do not create a pedning Payment in the db
       # we simulate a catastropic server crash where data was lost
       order_id = uuid.uuid4()

       stripe_event = {
              "type": "payment_intent.succeeded",
              "data": {
                     "object": {
                            "id": "pi_missing_data",
                            "amount": 10000,
                            "metadata": {"order_id": str(order_id)}
                     }
              }
       }

       handle_stripe_event(stripe_event)
       # 3 ASSERT: The system muust have have auto-rebuild the mission row
       payment = Payment.objects.get(transaction_id = "pi_missing_data")
       assert payment.status == "Success"
       assert payment.order_id == order_id
       # (10000 in paise / 100 = 100.00 normal formatting)
       assert float(payment.amount) == 100.00

       # 4: assert it also must have fired the outbox event to ship it

       assert PaymentEventOutbox.objects.count() == 1

@pytest.mark.django_db
def test_handle_stripe_event_payment_failed_updates_status():

       order_id = uuid.uuid4()
       Payment.objects.create(
              order_id = order_id,
              transaction_id = 'pi_webhook_test',
              status = "Pending",
              amount = 100.00
       )

       stripe_event = {
              "type": "payment_intent.payment_failed",
              "data": {
                     "object": {
                            "id" : "pi_webhook_test",
                            "amount": 10000,
                            "metadata": {"order_id": str(order_id)}
                     }      

              }
       }

       handle_stripe_event(stripe_event)

       payment = Payment.objects.get(transaction_id = "pi_webhook_test")
       assert payment.status == "Failed"
       assert payment.order_id == order_id
       # (10000 in paise / 100 = 100.00 normal formatting)
       assert float(payment.amount) == 100.00
       assert PaymentEventOutbox.objects.count() == 0