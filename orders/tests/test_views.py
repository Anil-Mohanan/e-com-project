from kombu import producers
from rest_framework.test import APITestCase,APIClient
from rest_framework import status 
from user_auth.tests.factories import UserFactory
from orders.tests.factories import OrderFactory,OrderItemFactory,ShippingAddressFactory
from product.tests.factories import ProductFactory,ProductVariantFactory
from unittest.mock import patch

class CartAPIIntegrationTest(APITestCase):
       def setUp(self):
              # Create two user: one to own the cart, one to try to hack it
              self.client = APIClient()
              self.user = UserFactory()
              self.hacker = UserFactory()
              self.client.force_authenticate(user = self.user)

       def test_autheticated_user_can_view_own_cart(self):

              product = ProductFactory()
              variant = ProductVariantFactory(product=product)
              
              order =  OrderFactory(user = self.user,status = 'Cart')
              OrderItemFactory(
                     order=order, 
                     product_id=product.id, 
                     variant_id=variant.id, 
                     quantity=2, 
                     price_at_purchase=None
              )

              response = self.client.get('/api/v1/orders/cart/')

              self.assertEqual(response.status_code,status.HTTP_200_OK)

              self.assertEqual(len(response.data['items']),1)
              self.assertEqual(response.data['items'][0]['quantity'],2)

       def test_empty_cart_creation_for_new_user(self):
              # 1. SETUP: We do nothing! The user logs in with a completely empty database.
              # 2. ACT: Hit the API
              response = self.client.get('/api/v1/orders/cart/')
              # 3. ASSERT: Does it crash? No! 
              # Your `get_or_create_cart` service should automatically build them an empty cart.
              self.assertEqual(response.status_code, status.HTTP_200_OK)
              self.assertEqual(response.data['status'], 'Cart')
              self.assertEqual(len(response.data['items']), 0) # No items yet!


       def test_unauthenticated_user_cannot_view_cart(self):

              self.client.force_authenticate(user = None) # logout the user we just logged in 

              response = self.client.get('/api/v1/orders/cart/')

              self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)

class AddtoCartAPIIntegrationTest(APITestCase):
       def setUp(self):
              self.client = APIClient()
              self.user = UserFactory()
              self.client.force_authenticate(user = self.user)
              # We need a REAL prodcut in the DB so the service doesn't crash!
              self.product = ProductFactory()
              self.variant = ProductVariantFactory(product = self.product)

       def test_add_item_to_cart_success(self):
              # 1 > SETUP: The JSON payload the frontend will send
              payload = {
                     'product_id': self.product.id,
                     'quantity': 3
              }
              # 2: ACT: Send a POST request to the endpoint
              response = self.client.post('/api/v1/orders/add_to_cart/',data=payload,format='json')

              #  3. ASSERT: Did the server accept the request?

              self.assertEqual(response.status_code, status.HTTP_200_OK)
              # 4. ASSERT: Did it return the new Cart JSON structure?
              self.assertEqual(response.data['status'],'Cart')
              self.assertEqual(len(response.data['items']),1)
              self.assertEqual(response.data['items'][0]['quantity'], 3)
       
       def test_add_missing_product_returns_404(self):

              payload = {
                     'product_id': 99999,
                     'quantity' : 1
              }
              
              response = self.client.post('/api/v1/orders/add_to_cart/',data = payload,format = 'json')

              self.assertEqual(response.status_code,status.HTTP_404_NOT_FOUND)

class CheckoutAPIIntegrationTest(APITestCase):
       def setUp(self):
              self.client = APIClient()
              self.user = UserFactory()

              self.client.force_authenticate(user = self.user)
              self.address = ShippingAddressFactory(user = self.user)
              self.product = ProductFactory()
              self.variant = ProductVariantFactory(product = self.product)
              self.order = OrderFactory(user = self.user,status = 'Cart')
              OrderItemFactory(
                     order = self.order,
                     product_id = self.product.id,
                     variant_id = self.variant.id,
                     quantity = 1,
                     price_at_purchase = None
              )
       @patch('orders.services.task_send_payment_success_email.delay')
       def test_successful_checkout(self,mock_email):
              payload = {
                     'address_id': self.address.id
              }
              response = self.client.post('/api/v1/orders/checkout/',data= payload,format='json')

              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(response.data['status'],'Pending')
              self.assertIsNotNone(response.data['shipping_address'])

       # ------------ Edge Case ----------- #
       def test_checkout_with_invalid_address_returns_404(self):
              payload = {'address_id': 99999} # Fake Address!

              response = self.client.post('/api/v1/orders/checkout/', data=payload, format='json')

              # Your orders/views.py currently catches this beautifully with a try/except!
              self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                           # FIX: Access the deeply nested message
              self.assertEqual(response.data['details']['non_field_errors'][0], 'Invalid Address ID')
              self.assertFalse(response.data['success'])

class CancelOrderAPIIntegrationTest(APITestCase):
       def setUp(self):
              self.client = APIClient()
              self.user = UserFactory()
              self.client.force_authenticate(user=self.user)

       def test_successful_order_cancellation(self):
              # 1. SETUP: Create a Pending order
              order = OrderFactory(user=self.user, status='Pending')

              # 2. ACT: Hit the detail POST endpoint 
              url = f'/api/v1/orders/{order.order_id}/cancel_order/'
              response = self.client.post(url)

              # 3. ASSERT: Did the View successfully format the Success Response?
              self.assertEqual(response.status_code, status.HTTP_200_OK)
              self.assertEqual(response.data['data']['new_status'], 'cancelled')

       def test_cannot_cancel_shipped_order(self):
              # 1. SETUP: Create a Shipped order
              order = OrderFactory(user=self.user, status='Shipped')

              # 2. ACT
              url = f'/api/v1/orders/{order.order_id}/cancel_order/'
              response = self.client.post(url)

              # 3. ASSERT: Expect HTTP 400 Bad Request
              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
              self.assertEqual(
                     response.data['details']['non_field_errors'][0], 
                     "Cannot Cancel order. It might be already Shipped or deliverd"
              )

class AdminActionAPIIntegrationTest(APITestCase):
       def setUp(self):
              self.client = APIClient()
              # Create two users: one normal customer, one admin!
              self.normal_user = UserFactory(is_staff=False)
              self.admin_user = UserFactory(is_staff=True)
              
              # The order belongs to the normal customer
              self.order = OrderFactory(user=self.normal_user, status='Pending')

       def test_normal_user_cannot_mark_as_paid(self):
              # 1. SETUP: Login as the regular customer
              self.client.force_authenticate(user=self.normal_user)

              # 2. ACT: Try to hack the payment endpoint
              url = f'/api/v1/orders/{self.order.order_id}/mark_as_paid/'
              response = self.client.patch(url)

              # 3. ASSERT: They must be blocked!
              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
              self.assertEqual(
                     response.data['details']['non_field_errors'][0], 
                     "Only Admin Can change the status"
              )

       def test_admin_user_can_mark_as_paid(self):
              # 1. SETUP: Login as the ADMIN
              self.client.force_authenticate(user=self.admin_user)

              # 2. ACT
              url = f'/api/v1/orders/{self.order.order_id}/mark_as_paid/'
              response = self.client.patch(url)

              # 3. ASSERT: The Admin is allowed to bypass
              self.assertEqual(response.status_code, status.HTTP_200_OK)
              self.assertEqual(response.data['data']['isPaid'], True)
