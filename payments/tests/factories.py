import factory 
from payments.models import Payment, PaymentEventOutbox

class PaymentFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = Payment
       
       order_id = factory.Faker('uuid4')
       transaction_id = factory.Sequence(lambda n: f'txn_stripe_{n}')
       payment_method = 'Stripe'
       amount = factory.Faker('pydecimal',left_digits=4,right_digits =2 ,positive = True)
       status = 'Pending'

class PaymentEventOutboxFactory(factory.django.DjangoModelFactory):
       class Meta:
              model = PaymentEventOutbox

       event_type = 'payment_intent.succeeded'
       payload = {}
       processed = False
       retry_count = 0