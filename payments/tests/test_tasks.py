import pytest
from unittest.mock import patch
from payments.models import PaymentEventOutbox
from payments.tasks import sweeper_payment_outbox
import uuid

@pytest.mark.django_db
@patch('payments.tasks.current_app.send_task')
def test_sweeper_payment_outbox_broadcasts_successfully(mock_send_task):
       # 1 Setup : Pin a sticky note to the crokboard
       order_id = str(uuid.uuid4())
       outbox_event = PaymentEventOutbox.objects.create(
              event_type = "payment.successful",
              payload = {"order_id" : order_id}
       )
       # 2: Act force the Background worker to run once

       sweeper_payment_outbox()

       # Assert  : did the messenger succsuflly yell across the building to the Orders app?
       # It must use the exact string name that the orders app excepts

       mock_send_task.assert_called_once_with(
              'orders.handle_payment_successful',
              args = [{'order_id' : order_id}]
       )

       # 4. ASSERT: Did the Messenger throw the sticky note in the trash? (processed = True)
       outbox_event.refresh_from_db()
       assert outbox_event.processed is True
       assert outbox_event.processed_at is not None

@pytest.mark.django_db
@patch('payments.tasks.current_app.send_task')
def test_sweeper_payment_outbox_handles_broadcast_failure(mock_send_task):
       order_id = str(uuid.uuid4())
       outbox_event = PaymentEventOutbox.objects.create(
              event_type="payment.successful",
              payload={"order_id": order_id}
       )
       
       # 1. SETUP: Simulate the Orders app crashing / throwing an Exception
       mock_send_task.side_effect = Exception("Orders app is offline")
       
       # 2. ACT
       sweeper_payment_outbox()
       
       # 3. ASSERT: The sticky note is NOT thrown in the trash (must stay processed=False)
       outbox_event.refresh_from_db()
       assert outbox_event.processed is False
       
       # 4. ASSERT: The retry_count incremented and the error was safely logged to the DB!
       assert outbox_event.retry_count == 1
       assert outbox_event.error_message == "Orders app is offline"

from payments.tasks import process_stripe_webhook_task

@patch('payments.tasks.handle_stripe_event')
def test_process_stripe_webhook_task_calls_service(mock_handle_stripe):
       # 1. ACT
       # Notice how we don't need a DB, just pass a fake dictionary
       process_stripe_webhook_task({"event": "fake"})
       
       # 2. ASSERT: Did the Celery task hand the dictionary off to the Service layer?
       mock_handle_stripe.assert_called_once_with({"event": "fake"})
