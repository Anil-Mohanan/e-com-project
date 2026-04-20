import factory
from orders.models import ShippingAddress, Order, OrderItem, OrderEventOutbox
from user_auth.tests.factories import UserFactory


class ShippingAddressFactory(factory.django.DjangoModelFactory):
       
       class Meta:
              model = ShippingAddress

       user = factory.SubFactory(UserFactory)
       full_name = factory.Faker('name')
       address_line_1 = factory.Faker('street_address')
       city = factory.Faker('city')
       state = factory.Faker('state')
       postal_code = factory.Faker('postcode')
       country = 'India'
       phone_number = factory.Faker('numerify',text='##########')
       is_default = False

class OrderFactory(factory.django.DjangoModelFactory):

       class Meta:
              model = Order
       
       user = factory.SubFactory(UserFactory)
       shipping_address = factory.SubFactory(ShippingAddressFactory)
       total_price = factory.Faker('pydecimal',left_digits = 4,right_digits = 2, positive = True)
       is_paid = False

class OrderItemFactory(factory.django.DjangoModelFactory):

       class Meta:
              model = OrderItem

       order = factory.SubFactory(OrderFactory)
       product_id = factory.Sequence(lambda n: n + 1)
       product_name = factory.Sequence(lambda n: f"product {n}")
       quantity = 2
       price_at_purchase = factory.Faker('pydecimal',left_digits = 4, right_digits = 2, positive = True)

class OrderEventOutboxFactory(factory.django.DjangoModelFactory):

       class Meta:
              model = OrderEventOutbox
       
       event_type = 'order_created'
       payload = {}
       processed = False
       retry_count = 0
       