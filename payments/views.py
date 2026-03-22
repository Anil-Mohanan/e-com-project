import stripe # The official library provided by Stripe to talk to their servers
from django.conf import settings # to access the keys in settings.py
from rest_framework.response import Response # To send JSON Back to the frontend
from rest_framework.views import APIView
from rest_framework import status , permissions
from django.shortcuts import get_object_or_404 # A helper to get the data or error out safely if missing
from django.http import HttpResponse # Standard Django response(not REST frame work) becasue Stripe expects a simple HTTP
from django.views.decorators.csrf import csrf_exempt # To disable seccurity ceck for this specific ulr
from django.utils.decorators import method_decorator # To apply the csrf_exempt decoratero to a class view
from orders.models import Order
from .models import Payment
from orders.emails import send_payment_success_email
from datetime import datetime
from config.utils import error_response ,success_response
import logging
from django.db import transaction
from .services import create_stripe_checkout,handle_stripe_event

stripe.api_key = settings.STRIPE_SECRET_KEY# verfining the Stripe keys 

logger = logging.getLogger(__name__)

class StripeCheckoutView(APIView):
       permission_classes = [permissions.IsAuthenticated]

       def post(self, request, *args, **kwargs):
              try:
                     order_id = request.data.get('order_id') # the frontend sends the {order_id : abcked0202}

                     #finding the order Safely
                     
                     payment = create_stripe_checkout(
                            user= request.user,
                            order_id= order_id
                     )
                     return Response(payment)
              except Order.DoesNotExist:
                     return error_response(message = "Order not found",status_code = 404)
              except ValueError as e:
                     return error_response(message = str(e),status_code = 404)
              except Exception as e:
                     #ERROR HANDINLING
                     #if Stripe is down, or keys are wrong, we catch the crash and tell the user.
                     return error_response(
                            message="Unable to initiate payment at this moment. Please try again",
                            status_code=500,
                            log_message=f"Stripe Checkout Failure for Order {order_id} : {e}"
                     )

#The Security Exception: telling Django to let in the Stripe request 
#Stripe dosen't have a CSRF token . disabling the The CSRF token check
#Question : what does this means by the Webhook
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
       
       permission_classes = [] # no permission check stripe is machine not a logged-in user
       
       def post(self, request, *args, **kwargs):
              # 1 Get the Raw Data
              # Question : Raw data are you talking about 
              payload = request.body
              
              # 2 Get the Security Stamp
              # Stripe sends a spcial header called 'Stripe-Signature'.
              # This proves the message actually come from Stripe 
              sig_header = request.META.get('HTTP_STRIPE_SIGNATURE') # Stripe doesn't just send data; they "sign" it using a secret mathematical formula

              # 3 Get Your Secret Key
              
              endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
              
              event = None # Declared varible set it to None

              try:
                     # 4 Verify the Signature: Checks Does (Payload + Secret) match the Signature? if yes real if no it's a fake
                     event = stripe.Webhook.construct_event(
                            payload, sig_header, endpoint_secret# It runs the math. If the math matches: It converts the raw text into a Python Object (dictionary) and returns it. If the math fails: It crashes immediately (raises an error), stopping the hacker.
                     )
                     print(event)

              except ValueError as e:
                     # if the payload was empty or garbage JSON
                     return HttpResponse(status=400)
              except stripe.error.SignatureVerificationError as e:
                     # if the signature didn't match
                     return HttpResponse(status=400)
              
              # 5 Handle The Event
              handle_stripe_event(event)
              return HttpResponse(status= 200)
              
