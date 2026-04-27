import stripe
from django.conf import settings
from abc import ABC, abstractmethod

# DEPENDENCY INVERSION: We define the "Interface" first.
class PaymentStrategy(ABC):
       @abstractmethod
       def create_checkout(self,user,order_data,repo):
              pass

# OPEN/CLOSED: We create a specific plugin for Stripe. 
# Tomorrow we can create PayPalPaymentStrategy without changing existing code!

class StripePaymentStrategy(PaymentStrategy):
       def create_checkout(self,user,order_data,repo):

              amount_in_paise = int(order_data['total_price'] * 100)

              intent = stripe.PaymentIntent.create(
                     amount = amount_in_paise,
                     currency = 'inr',
                     metadata = {
                            'order_id': str(order_data['order_id']),
                            'user_email': user.email
                     },
                     idempotency_key = f"intent_{order_data['order_id']}"
              )

              defaults = {
                     'payment_method': 'Stripe',
                     'amount': order_data['total_price'],
                     'status' : 'Pending',
                     'transaction_id': intent['id']
              }
              repo.create_or_update_payment(order_data['order_id'],defaults)

              return {
                     'client_secret' : intent['client_secret'],
                     'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
                     'gateway': 'stripe'
              }