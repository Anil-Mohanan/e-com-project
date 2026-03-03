from django.test import TestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from orders.models import Order, OrderItem
from product.models import Product, Category
from django.core.cache import cache
from decimal import Decimal
from unittest.mock import patch

User = get_user_model()

class DashboardSummaryTests(TestCase):
       def setUp(self):
              
              self.url = reverse('dahsboard-summary')

              self.client = APIClient()

              self.user = User.objects.create_superuser(
                     email = 'testadmin@gmail.com',
                     password =  'pas130@132002'
              )

              self.client.force_authenticate(user=self.user)

              cache.clear()

       def test_admin_can_access_dashboard_summary(self): # Happy Path
              """Test that Admin can acess the DashBoard summary""" 

              cache.clear()

              response = self.client.get(self.url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)

       def test_returns_corrent_total_revenue(self): # Happy Path
              """Test that the dahsboard correntily calculate total revenue from valid orders"""

              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=100.00,stock=10)# Create a Fake product

              order = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt a valid sale

              OrderItem.objects.create(
                     order= order, 
                     product= produtct,
                     quantity= 1
              )
              response = self.client.get(self.url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)

              self.assertEqual(response.data['total_revenue'],Decimal(218))

       def test_returns_correct_total_orders(self):

              cache.clear()

              #valid_orders
              order1 = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt 
              order2 = Order.objects.create(user = self.user, status = "Pending") #Creating a fake Delivered Order to reperesnt
              order3 = Order.objects.create(user = self.user, status = "Shipped") #Creating a fake Delivered Order to reperesnt

              # invalid orders
              order4 = Order.objects.create(user = self.user, status = "Cart") #Creating a fake Delivered Order to reperesnt
              order5 = Order.objects.create(user = self.user, status = "Cancelled") #Creating a fake Delivered Order to reperesnt

              response = self.client.get(self.url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)

              self.assertEqual(response.data['total_orders'],3)

       def test_returns_correct_total_product(self):
              
              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              #valid products
              produtct1 = Product.objects.create(category=category,name = "Test Product1", slug = "test-product1", price=100.00,stock=10)# Create a Fake product
              produtct2 = Product.objects.create(category=category,name = "Test Product2", slug = "test-product2", price=100.00,stock=10)# Create a Fake product

              #invalid Product
              produtct3 = Product.objects.create(category=category,name = "Test Product3", slug = "test-product3", price=100.00,stock=10,is_active=False)# Create a Fake product
              produtct = Product.objects.create(category=category,name = "Test Product4", slug = "test-product4", price=100.00,stock=10,is_active=False)# Create a Fake product

              response = self.client.get(self.url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(response.data['total_products'],2)

       def test_return_correct_total_users(self):
              cache.clear()

              user1 = User.objects.create_user(email = 'user1@gmail.com', password = 'adi212oidfa;f')
              user2 = User.objects.create_user(email = 'user2@gmail.com', password = 'sdjfiad2jd#2kd')
              user3 = User.objects.create_user(email = 'user3@gmail.com', password = 'jdlkfjas2#jdi')
              user4 = User.objects.create_user(email = 'user4@gmail.com', password = 'adi212oidfajlda')

              user5 = User.objects.create_superuser(email = 'user5@gmai.com', password = 'djkaiqie132@')
              
              respose = self.client.get(self.url)

              self.assertEqual(respose.status_code,status.HTTP_200_OK)
              self.assertEqual(respose.data['total_users'],4)

       def test_return_only_valid_sales(self):
              cache.clear()

               #valid_orders
              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=100.00,stock=10)# Create a Fake product

              order = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt a valid sale

              OrderItem.objects.create(
                     order= order, 
                     product= produtct,
                     quantity= 1
              ) #Creating a fake Delivered Order to reperesnt

              # invalid orders
              order4 = Order.objects.create(user = self.user, status = "Cart") #Creating a fake Delivered Order to reperesnt
              order5 = Order.objects.create(user = self.user, status = "Cancelled") #Creating a fake Delivered Order to reperesnt

              OrderItem.objects.create(
                     order = order4,
                     product=produtct,
                     quantity=1
              )
              OrderItem.objects.create(
                     order=order5,
                     product=produtct,
                     quantity=1
              )
              response = self.client.get(self.url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(response.data['total_revenue'],Decimal(218))

       def test_return_zero_revenue(self):
              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=100.00,stock=10)# Create a Fake product

              order4 = Order.objects.create(user = self.user, status = "Cart") #Creating a fake Delivered Order to reperesnt
              order5 = Order.objects.create(user = self.user, status = "Cancelled") #Creating a fake Delivered Order to reperesnt

              OrderItem.objects.create(
                     order = order4,
                     product=produtct,
                     quantity=1
              )
              OrderItem.objects.create(
                     order=order5,
                     product=produtct,
                     quantity=1
              )
              response = self.client.get(self.url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(response.data['total_revenue'],0)

       def test_sum_of_multiple_orders(self):
              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=100.00,stock=10)# Create a Fake product

              order4 = Order.objects.create(user = self.user, status = "Shipped") #Creating a fake Delivered Order to reperesnt
              order5 = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt

              OrderItem.objects.create(
                     order = order4,
                     product=produtct,
                     quantity=1
              )
              OrderItem.objects.create(
                     order=order5,
                     product=produtct,
                     quantity=1
              )
              response = self.client.get(self.url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(response.data['total_revenue'],Decimal(436))
       
       def test_cache_response_returned(self): # withing time out
              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=100.00,stock=10)# Create a Fake product

              order4 = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt
              

              OrderItem.objects.create(
                     order = order4,
                     product=produtct,
                     quantity=1
              )

              response = self.client.get(self.url)
              response2 = self.client.get(self.url)

              self.assertEqual(response2.status_code,status.HTTP_200_OK)
              self.assertEqual(response2.data['total_revenue'],Decimal(218))

       def test_cache_invaildates(self):#After time out
              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=100.00,stock=10)# Create a Fake product

              order4 = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt
              

              OrderItem.objects.create(
                     order = order4,
                     product=produtct,
                     quantity=1
              )

              response = self.client.get(self.url)


              cache.clear()

              order5 = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt
              order6 = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt
              order7 = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt

              OrderItem.objects.create(
                     order = order5,
                     product=produtct,
                     quantity=1
              )
              OrderItem.objects.create(
                     order = order6,
                     product=produtct,
                     quantity=1
              )
              OrderItem.objects.create(
                     order = order7,
                     product=produtct,
                     quantity=1
              )
              response2 = self.client.get(self.url)

              self.assertEqual(response2.status_code,status.HTTP_200_OK)
              self.assertEqual(response2.data['total_revenue'],Decimal(872))


              
#--------------------EDGE_CASE-----------------------#

       def test_total_price_contains_decimal(self):#values

              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=Decimal('100.99'),stock=10)# Create a Fake product

              order = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt

              OrderItem.objects.create(
                     order = order,
                     product=produtct,
                     quantity=1
              )

              response = self.client.get(self.url)

              self.assertEqual(response.data['total_revenue'],Decimal('219.17'))

       def test_negative_order_value(self):

              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=Decimal('100.00'),stock=10)# Create a Fake product

              order = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt

              OrderItem.objects.create(
                     order = order,
                     product=produtct,
                     quantity=1
              )

              order1 = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt

              OrderItem.objects.create(
                     order = order1,
                     product=produtct,
                     quantity=1,
                     price_at_purchase=Decimal('-100.00')
              )
              response = self.client.get(self.url)

              self.assertEqual(response.data['total_revenue'],Decimal(200))

       def test_very_large_revenue_values(self):

              cache.clear()

              category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

              produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=Decimal('9999999.99'),stock=10)# Create a Fake product

              order = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt

              OrderItem.objects.create(
                     order = order,
                     product=produtct,
                     quantity=1
              )

              response = self.client.get(self.url)

              self.assertEqual(response.data['total_revenue'],Decimal('11799999.99'))

       # def test_order_exit_total_price_null(self):
       
       #        cache.clear()

       #        category = Category.objects.create(name = "TestCategory", slug = "test-category") # Creating a Fake category

       #        produtct = Product.objects.create(category=category,name = "Test Product", slug = "test-product", price=100,stock=10)# Create a Fake product

       #        order = Order.objects.create(user = self.user, status = "Delivered") #Creating a fake Delivered Order to reperesnt

       #        Order.objects.all().update(total_price=None)

       #        response = self.client.get(self.url)
       
       #        self.assertEqual(response.data['total_revenue'],0)
              
       @patch('analytics.views.Order.objects.valid_sales')
       def test_database_failure_triggers_error_response(self, mock_valid_sales):
              cache.clear()

              # We are programming our fake "Mock" database to literally explode
              # The moment the API tries to calculate revenue, it will throw an Exception!
              mock_valid_sales.side_effect = Exception("CRITICAL DATABASE FAILURE!")

              response = self.client.get(self.url)

              # The assertion: Does our decorator catch it?
              self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
              
              self.assertEqual(response.data['error'], 'There is An Error occured in Calculation')
