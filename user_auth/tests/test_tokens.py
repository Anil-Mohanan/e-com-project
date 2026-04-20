from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import override_settings


@override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_CLASSES': [], 'DEFAULT_THROTTLE_RATES': {}})

class TokenTests(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="token@test.com",
            password="Password123"
        )

        self.refresh = RefreshToken.for_user(self.user)
        self.access = str(self.refresh.access_token)

    def test_access_token_allows_request(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access}")

        url = reverse("profile", kwargs={'version': 'v1'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake.token.here")

        url = reverse("profile", kwargs={'version': 'v1'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

