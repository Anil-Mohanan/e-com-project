from orders.services import mark_as_paid_process
from math import prod
from django.test import TestCase
from unittest.mock import patch
from orders.services import add_to_cart_process, process_checkout,cancel_order_process,update_quantity_process,remove_item_process,update_status_process
from orders.tests.factories import OrderFactory, OrderItemFactory, ShippingAddressFactory
from user_auth.tests.factories import UserFactory
from orders.models import OrderItem, Order, OrderEventOutbox

class AddToCartProcessTests(TestCase):

       def setUp(self):
              self.user = UserFactory()

       @patch('orders.services.get_product_details') # This is Python magic. It says "When orders.services tries to call get_product_details, intercept it!"
       def test_add_new_item_to_empty_cart(self,mock_get_details):
              mock_get_details.return_value = {
                     'name' : 'Test Gaming Mouse',
                     'price': '50.00'
              }

              order,item = add_to_cart_process(
                     user = self.user,
                     product_id= 99,
                     quantity= 2
              )

              self.assertEqual(order.status,'Cart')
              self.assertEqual(item.product_name,'Test Gaming Mouse')
              self.assertEqual(item.quantity,2)
              self.assertEqual(item.product_id,99)

              mock_get_details.assert_called_once_with(99)

       # ------------- Edge Case ---------------------- #
       @patch('orders.services.get_product_details')
       def test_add_existing_item_increments_quantity(self,mock_get_details):

              mock_get_details.return_value = {

                     'name': 'Test Gaming Mouse',
                     'price' : '50.00'
              }

              add_to_cart_process(user = self.user, product_id=99,quantity=2)

              order,item = add_to_cart_process(user=self.user,product_id=99, quantity=3)

              self.assertEqual(item.quantity,5)

              self.assertEqual(order.items.count(),1)

class ProcessCheckoutTests(TestCase):

       def setUp(self):
              self.user = UserFactory()
              self.address = ShippingAddressFactory(user = self.user)
              self.order = OrderFactory(user = self.user, status = 'Cart')
              self.item = OrderItemFactory(order = self.order,product_id = 99, quantity = 2, price_at_purchase = None)
       
       @patch('orders.services.get_product_details')

       @patch('orders.services.task_send_payment_success_email.delay')

       def test_successful_checkout(self,mock_email_delay,mock_get_details):

              mock_get_details.return_value = {

                     'name': 'Test Item',
                     'price': '100.00'
              }
              with self.captureOnCommitCallbacks(execute=True):

                     processed_order = process_checkout(user = self.user,address_id=self.address.id)

              self.assertEqual(processed_order.status,'Pending')
              self.assertEqual(processed_order.shipping_address, self.address)

              self.item.refresh_from_db()

              self.assertEqual(self.item.price_at_purchase,100)

              outbox_event = OrderEventOutbox.objects.last()

              self.assertIsNotNone(outbox_event)

              self.assertEqual(outbox_event.event_type,'order.placed')

              self.assertEqual(outbox_event.payload['order_id'],str(processed_order.order_id))

              self.assertEqual(outbox_event.payload['user_id'],self.user.id)

              mock_email_delay.assert_called_once_with(processed_order.order_id)


       # --------------- Edge Case ----------------- #

       @patch('orders.services.get_product_details')
       @patch('orders.services.task_send_payment_success_email.delay')

       def test_checkout_returns_existing_pending_order(self,mock_email,mock_get_details):

              # 1. SETUP: The user ALREADY has a Pending order in the DB
              existing_order = OrderFactory(user = self.user, status = 'Pending')
              # 2. ACT: They try to checkout again
              result = process_checkout(user = self.user, address_id=self.address.id)
               # 3. ASSERT: It intercepted it and returned the existing one!
              self.assertEqual(result.id,existing_order.id)
              # Prove it didn't do any new processing (no new messages sent to Outbox!)
              self.assertEqual(OrderEventOutbox.objects.count(),0)

       # Note we are mocking 'cache.add', which is what process_checkout uses
       @patch('orders.services.cache.add')
       def test_checkout_blocked_by_redis_lock(self,mock_cache_add):

              # 1. Fake Redis saying "NO, this key is already locked by another thread!"
              mock_cache_add.return_value = False

              # 2. ACT & ASSERT: It MUST crash with our specific ValueError

              with self.assertRaises(ValueError) as context:

                     process_checkout(user = self.user,address_id = self.address.id)

              self.assertEqual(str(context.exception),"Checkout already in progress. Please wait.")

class CancelOrderProcessTests(TestCase):

       def setUp(self):
              self.user = UserFactory()
              self.address = ShippingAddressFactory(user = self.user)
              self.order = OrderFactory(user = self.user, status = 'Pending')
              self.item = OrderItemFactory(order = self.order,product_id = 99, quantity = 2, price_at_purchase = "100.00")

       @patch('orders.services.task_cancellation_email.delay')
       def test_successful_cancellation(self,mock_cancel_email):

              with self.captureOnCommitCallbacks(execute=True):
                     canceled_order = cancel_order_process(self.order)

              self.assertEqual(canceled_order.status,"Cancelled")

              outbox_event = OrderEventOutbox.objects.last()

              self.assertIsNotNone(outbox_event)

              self.assertEqual(outbox_event.event_type,'order.cancelled')

              mock_cancel_email.assert_called_once_with(canceled_order.order_id)

       @patch('orders.services.task_cancellation_email.delay')
       def test_idempotent_cancellation_security(self,mock_cacnel_email):
              
              cancel_order_process(self.order)

              cancel_order_process(self.order)

              outbox_count = OrderEventOutbox.objects.filter(event_type = 'order.cancelled').count()

              self.assertEqual(outbox_count,1)


class MarkAsPaidProcessTests(TestCase):
       def setUp(self):
              self.user = UserFactory()
              self.order = OrderFactory(user = self.user, status = 'Pending',is_paid = False,paid_at=None)
              self.itme = OrderItemFactory(order = self.order)

       @patch('orders.services.task_send_payment_success_email.delay')
       def test_successful_payment_processing(self,mock_email):

              with self.captureOnCommitCallbacks(execute=True):
                     paid_order = mark_as_paid_process(self.order)

              self.assertTrue(paid_order.is_paid)
              self.assertIsNotNone(paid_order.paid_at)

              outbox_event = OrderEventOutbox.objects.last()
              
              self.assertIsNotNone(outbox_event)

              self.assertEqual(outbox_event.event_type,'order.completed')

              mock_email.assert_called_once_with(paid_order.order_id)

       @patch('orders.services.task_send_payment_success_email.delay')
       def test_idempotent_payment_stops_duplicate_emails(self,mock_email):
              with self.captureOnCommitCallbacks(execute=True):
                     mark_as_paid_process(self.order)

                     mark_as_paid_process(self.order)

              self.assertEqual(mock_email.call_count,1)

              outbox_count = OrderEventOutbox.objects.filter(event_type = 'order.completed').count()

              self.assertEqual(outbox_count,1)

class UpdateQuantityProcessTests(TestCase):
       def setUp(self):
              self.user = UserFactory()
              self.order = OrderFactory(user = self.user, status = 'Cart')
              self.item = OrderItemFactory(order = self.order,product_id = 99,quantity = 5)

       def test_update_quantity_success(self):
              # Act: Change the quantity to 10
              order, item = update_quantity_process(self.user, product_id=99,quantity=10)
              
              self.assertEqual(item.quantity,10)

       def test_update_quantity_to_zero_deletes_item(self):
              # Act: Change quantity to 0
              update_quantity_process(self.user,product_id=99,quantity=0)
              self.assertEqual(self.order.items.count(),0)
       
class RemoveItemProcessTests(TestCase):
       def setUp(self):
              self.user = UserFactory()
              self.order = OrderFactory(user = self.user, status = 'Cart')
              self.item = OrderItemFactory(order = self.order, product_id = 99)

       def test_remove_item_success(self):
              remove_item_process(self.user,product_id = 99)
              self.assertEqual(self.order.items.count(),0)

class UpdateStatusProcessTests(TestCase):
       def setUp(self):
              self.user = UserFactory()
              self.order = OrderFactory(user=self.user, status='Pending')

       def test_update_status_simple(self):
              # Just a normal status update to 'Pending' -> 'Delivered'
              updated_order = update_status_process(self.order, "Delivered")
              self.assertEqual(updated_order.status, "Delivered")

       @patch('orders.services.task_send_shipping_email.delay')
       def test_update_status_to_shipped_triggers_email(self, mock_shipping_email):
              # Act: Update status exactly to 'Shipped'
              updated_order = update_status_process(self.order, "Shipped")
              
              self.assertEqual(updated_order.status, "Shipped")
              # Assert the email task was triggered
              mock_shipping_email.assert_called_once_with(self.order.order_id)
