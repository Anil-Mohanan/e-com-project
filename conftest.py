# Root conftest.py — shared fixtures across all apps
# Factories and fixtures will be added here as we build tests
import pytest
from rest_framework.test import APIClient
from user_auth.tests.factories import UserFactory
from django.core.cache import cache


@pytest.fixture
def logged_in_client():
       """
       A pytest fixutre that creates a user, authenticates them,
       and returns both the client and the user.
       """
       client = APIClient()
       user = UserFactory()
       client.force_authenticate(user=user)

       return {
              'client': client,
              'user':user
       }
@pytest.fixture
def api_client():
       """Returns an unauthenticated DRF APIClient."""
       return APIClient()

@pytest.fixture(autouse=True)
def clear_cache():
    from django.core.cache import cache
    cache.clear()

@pytest.fixture
def admin_client():
       """Fixture for staff-only endpoints."""
       client = APIClient()
       admin = UserFactory(is_staff=True, is_superuser=True)
       client.force_authenticate(user=admin)
       return client
