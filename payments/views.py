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
from config.utils import error_response
import logging

stripe.api_key = settings.STRIPE_SECRET_KEY# verfining the Stripe keys 

logger = logging.getLogger(__name__)

class StripeCheckoutView(APIView):
       permission_classes = [permissions.IsAuthenticated]

       def post(self, request):
              try:
                     order_id = request.data.get('order_id') # the frontend sends the {order_id : abcked0202}

                     #finding the order Safely
                     
                     order = get_object_or_404(Order,order_id = order_id, user=request.user)#looking for an order that mateches the ID and belongs to this spefic user 
                     
                     # PREVENT DOUBLE PAYMENTS
                     #cheking if this order already has "Success" paymet linked to it.
                     # 'hasster' checks if the 'payment relationship exists in the DB.
                     if order.is_paid:
                            return Response({"error": "This order is already paid."},status=400)
                     
                     payment = getattr(order, 'payment',None)
                     if payment and payment.status == 'Success': 
                            return Response(
                                   {"error": "This order is already paid."},
                                   status=status.HTTP_400_BAD_REQUEST
                            )
                     # CONVERT PRICE TO SMALLES UNIT
                     #stripe does not handle decimals like 100.50 it wants integers.
                     amount_in_paise= int(order.total_price * 100)

                     # CREATE THE "PAYMENT INTENT" (talking to stripe)
                     # telling to stripe i want to collect moneny
                     # stripe replay with pending transaction id 
                     
                     intent = stripe.PaymentIntent.create( # Question: what is payment intent. what is pending transaction id how does the stripe have that, Answer: payment intnent like a restauruant bill we creating a new bill using the .create() function 
                            amount= amount_in_paise,
                            currency='inr',
                            metadata={
                                   # attaching data to the payment so we can find it int he strpe dashboard
                                   'order_id': str(order.order_id),
                                   'user_email': request.user.email
                            }
                     )
                     
                     # SAVE RECORED INTO DB
                     #update_or_create : if they tried to bfore (failed), we update that row, if new we create it
                     Payment.objects.update_or_create(
                            order = order,
                            defaults={
                                   'payment_method': 'Stripe',
                                   'amount': order.total_price ,# Store the normal decimal value
                                   'status' : 'Pending', # it is not successful yet.the user still has to type their card details
                                   'transaction_id' : intent['id'] # important : Stored "pi..." so we can track it later ---- question what is this Answer: the id of the payment did buy the user on stripe 
                            }
                     )
                     # SEND THE KEYS TO FRONTEND
                     # sending the two keys to the react:
                     # client_secret: the unique key for this transaction 
                     # stripe_public_key : the generic key to show the payment form.
                     
                     return Response({
                            'client_secret' : intent['client_secret'],
                            'stripe_public_key' : settings.STRIPE_PUBLIC_KEY
                     })
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
       
       def post(self,request):
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

              #Case A: Payment Succeeded
              if event['type'] == 'payment_intent.succeeded':
                     intent = event['data']['object'] # The Payment details 

                     transaction_id = intent['id']
                     order_id = intent['metadata'].get('order_id') # Create the metadat in StripeCheckoutView
                     
                     #Step A1 Mark payment as 'Success' DB
                     try:
                            payment = Payment.objects.get(transaction_id =  transaction_id)
                            payment.status = 'Success'
                            payment.save()
                     except Payment.DoesNotExist:
                            logger.warning(f"Payment record missing for transaction {transaction_id}, but Stripe succeeded.")
                     except Exception as e:
                            logger.error(f"Unexpected error updating Payment {transaction_id}: {e}")
                            #Step A2 Mark order As pending
                     try:
                            order = Order.objects.get(order_id = order_id)
                            order.status = 'Pending'
                            order.is_paid = True
                            order.paid_at = datetime.now()
                            order.save()
                            try:
                                   send_payment_success_email(order)
                            except Exception as e:
                                   logger.error(f"Failed to send email for Order {order_id}: {e}")
                     except Order.DoesNotExist:
                            logger.error(f"CRITICAL: Stripe succeeded but Order {order_id} not found in DB!")
                     except Exception as e:
                            logger.error(f"Error updating Order {order_id} in webhook: {e}")
                     return HttpResponse(status = 200)
              
                           #Case B: Payment Failed (Card Declined , Insufficient funds)
              elif event['type'] == 'payment_intent.payment_failed':
                     intent = event['data']['object']
                     transaction_id = intent['id']
                     errror_message = intent.get('last_payment_error', {}).get('message','Unknow error')
                     try:
                     #mark the payment as Failed 
                            payment = Payment.objects.get(transaction_id = transaction_id)
                            payment.status = 'Failed'
                            payment.save()
                            logger.warning(f"payment Faild for Transaction {transaction_id}: {errror_message}")
                     except Payment.DoesNotExist:
                            logger.error(f"Webhook received failure for unknown Transaction {transaction_id}")
                            return HttpResponse(status = 200)
                     except Exception as e:
                            logger.error(f"Unexpected DB error in Webhook failure case: {e}")
                            return HttpResponse(status=200)  # Stripe will keep re-sending the "Payment Success" webhook every hour for roughly 3 days until your server finally replies with "200 OK" (which means "I got it, stop yelling"). 
              