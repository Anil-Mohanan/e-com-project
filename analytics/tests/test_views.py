import pytest
from django.urls import reverse
from rest_framework import status
from product.tests.factories import ProductFactory
from user_auth.tests.factories import UserFactory
from django.contrib.auth import get_user_model
from analytics.user_services import get_total_customers_count
from orders.tests.factories import OrderFactory
from django.utils import timezone
from datetime import timedelta
from orders.models import Order 
from decimal import Decimal

User = get_user_model()

@pytest.mark.django_db
class TestAnalyticsPermissions:
       """SECURITY: Ensuring the Admin Dashboard is actually locked"""
       
       def test_guest_cannot_access_summary(self, api_client):
              """EDGE CASE: Anonymous user blocked"""
              url = reverse('dashboard-summary', kwargs={'version': 'v1'})
              response = api_client.get(url)
              assert response.status_code == status.HTTP_401_UNAUTHORIZED

       def test_regular_user_cannot_access_summary(self, logged_in_client):
              """EDGE CASE: Normal customer blocked from Admin Intel"""
              url = reverse('dashboard-summary', kwargs={'version': 'v1'})
              response = logged_in_client['client'].get(url)
              assert response.status_code == status.HTTP_403_FORBIDDEN

       def test_admin_access_success(self, admin_client):
              """HAPPY PATH: Only staff can see the numbers"""
              url = reverse('dashboard-summary', kwargs={'version': 'v1'})
              # Using the new admin_client we just created!
              response = admin_client.get(url)
              
              assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestDashboardSummary:
       """Verifying the 'Big Numbers' calculation"""
       def test_summary_data_accuracy(self, admin_client):
              # 1. SETUP: Create ONE seller to rule them all
              seller = UserFactory(is_staff=False) 
              
              initial_user_count = get_total_customers_count()
              
              # Pass the seller to the ProductFactory so it doesn't create new ones!
              ProductFactory.create_batch(3, is_active=True, seller=seller)
              
              # Create 2 more regular customers
              UserFactory.create_batch(2, is_staff=False)
              
              url = reverse('dashboard-summary', kwargs={'version': 'v1'})
              response = admin_client.get(url)
              
              # Now the math will be: initial_count(1 seller) + 2 new customers = 3
              assert response.status_code == status.HTTP_200_OK
              
              # 1. Check Users (Math should be: 1 seller + 2 customers = 3)
              assert response.data['total_users'] == initial_user_count + 2
              
              # 2. Check Products (We created 3)
              assert response.data['total_products'] == 3
              
              # 3. Check Financials (Should be zero for now)
              assert response.data['total_orders'] == 0
              assert response.data['total_revenue'] == 0

       def test_summary_ignores_inactive_products(self, admin_client):
              """EDGE CASE: Inactive products shouldn't show up in metrics"""
              ProductFactory(is_active=True)
              ProductFactory(is_active=False) # Should be ignored
              
              url = reverse('dashboard-summary', kwargs={'version': 'v1'})
              response = admin_client.get(url)
              
              assert response.data['total_products'] == 1
       
