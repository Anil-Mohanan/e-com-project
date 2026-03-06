import stripe # The official library provided by Stripe to talk to their servers
from django.conf import settings # to access the keys in settings.py
from orders.models import Order
from orders.emails import send_payment_success_email
from datetime import datetime
from django.db import transaction
from .models import Payment
import logging

logger = logging.getLogger(__name__)


def create_stripe_checkout(user,order_id):
       order = Order.objects.get(order_id=order_id,user=user)#looking for an order that mateches the ID and belongs to this spefic user 
                     
                     # PREVENT DOUBLE PAYMENTS
                     #cheking if this order already has "Success" paymet linked to it.
                     # 'hasster' checks if the 'payment relationship exists in the DB.
       if order.is_paid:
              raise ValueError("This order is already paid")
       
       payment = getattr(order, 'payment',None)
       if payment and payment.status == 'Success': 
              raise ValueError("This order is already paid")

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
                     'user_email': user.email
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
       
       return {
              'client_secret' : intent['client_secret'],
              'stripe_public_key' : settings.STRIPE_PUBLIC_KEY
       }

def handle_stripe_event(event):
       if event['type'] == 'payment_intent.succeeded':
              intent = event['data']['object'] # The Payment details 
              transaction_id = intent['id']
              order_id = intent['metadata'].get('order_id') # Create the metadat in StripeCheckoutView
              
              #Step A1 Mark payment as 'Success' DB
              try:
                     with transaction.atomic():
                            payment = Payment.objects.select_for_update().get(transaction_id=transaction_id)
                            if payment.status == "Success": 
                                   return 
                            else:
                                   payment.status = "Success"
                                   payment.save()
                            #Step A2 Mark order As pending
                            order = Order.objects.get(order_id = order_id)
                            order.status = 'Pending'
                            order.is_paid = True
                            order.paid_at = datetime.now()
                            order.save()
                     try:
                            send_payment_success_email(order)
                     except Exception as e:
                            logger.error(f"Failed to send email for Order {order_id}: {e}")
              except Payment.DoesNotExist:
                     logger.warning(f"Payment record missing for transaction {transaction_id}, but stripe,succeeded")
              
              except Order.DoesNotExist:
                     logger.error(f"CRITICAL: Stripe succeeded but order {order_id} not found in DB!")
              except Exception as e:
                     logger.error(f"Unexpected DB Error while writing Webhook Data: {e}")
              return 
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
                     return 
              except Exception as e:
                     logger.error(f"Unexpected DB error in Webhook failure case: {e}")
                     return # Stripe will keep re-sending the "Payment Success" webhook every hour for roughly 3 days until your server finally replies with "200 OK" (which means "I got it, stop yelling"). 
       