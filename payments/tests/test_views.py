from django.http import response
from kombu import uuid
import pytest
import stripe
import uuid
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch

# We don't use 'logged_in_clien

@pytest.fixture
def api_client():
       return APIClient()

@pytest.mark.django_db
def test_stripe_webhook_rejects_hackers(api_client):
       # 1. SETUP: A fake hacker payload
       payload = {"type": "checkout.session.completed"}

       # 2. Act: Hacker hits the URL Withoug the cryptographic Stripe Signatuer!
       # (Check your urls.py if your webhook paht is different!)
       response = api_client.post('/api/v1/payments/webhook/',data = payload,format = 'json')
       # 3. ASSERT: Django MUST reject it instantly with a 400 Bad Request
       assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
@patch('payments.views.stripe.Webhook.construct_event')
@patch('payments.views.process_stripe_webhook_task.delay')
def test_stripe_webhook_accepts_valid_signature(mock_task_delay, mock_stripe_verify, api_client):
       # 1. SETUP: We tell Pytest to "hijack" the Stripe mathematical verification
       # and just pretend it succeeded, passing back a fake Stripe Event.
       mock_stripe_verify.return_value = {"id": "evt_123", "type": "checkout.session.completed"}
       
       # 2. ACT: Hit the Webhook WITH a fake signature header
       response = api_client.post(
              '/api/v1/payments/webhook/',
              data="{}", 
              content_type='application/json',
              HTTP_STRIPE_SIGNATURE='t=123,v1=secret_hacker_math'
       )
       
       # 3. ASSERT: The server accepted it!
       assert response.status_code == status.HTTP_200_OK
       
       # 4. ASSERT: Did it trigger the background Celery Worker?
       assert mock_task_delay.call_count == 1

@pytest.mark.django_db
@patch('payments.views.create_stripe_checkout')
def test_stripe_checkout_success(mock_create_checkout,logged_in_client):

       #1. Setup : inctercept the network call and return a fake stripe Dcitonary
       mock_create_checkout.return_value = {
              "checkout_url": "https://checkout.stripe.com/fake123"
       }
       client = logged_in_client['client']
       payload = {"order_id": str(uuid.uuid4())}
       response = client.post('/api/v1/payments/create-payment-intent/',data = payload,format = 'json')

       assert response.status_code == status.HTTP_200_OK
       assert response.data['checkout_url'] == "https://checkout.stripe.com/fake123"


@pytest.mark.django_db
@patch('payments.views.create_stripe_checkout')
def test_stripe_checkout_handles_service_error_beautifully(mock_create_checkout, logged_in_client):
       # 1. SETUP: Pretend the Service crashed because the Hacker tried to pay for an already-paid order
       mock_create_checkout.side_effect = ValueError("Order is already paid")
       
       # 2. ACT
       client = logged_in_client['client']
       payload = {"order_id": str(uuid.uuid4())}
       response = client.post('/api/v1/payments/create-payment-intent/', data=payload, format='json')
       
       # 3. ASSERT: Did the View catch the crash and format it into a clean HTTP 404?
       assert response.status_code == status.HTTP_404_NOT_FOUND
       assert response.data['details']['non_field_errors'][0] == "Order is already paid"