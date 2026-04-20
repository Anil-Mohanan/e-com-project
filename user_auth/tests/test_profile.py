from django.http import response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user_auth.serializers import CustomTokenObtainPairSerializer
from user_auth.tests.factories import UserFactory

class ProfileAPITests(APITestCase):
       def test_get_user_profile(self):

              user = UserFactory()

              refresh_token = CustomTokenObtainPairSerializer.get_token(user)
              access_token = str(refresh_token.access_token)

              self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

              url = reverse('profile', kwargs={'version': 'v1'})
              response = self.client.get(url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(response.data['email'],user.email)
       
       def test_get_user_profile_edge_case(self):
              email = 'user1exaple@gmail.com'
              password = 'user5678exapmle'

              user = UserFactory()
              self.client.credentials()

              url = reverse('profile', kwargs={'version': 'v1'})
              response = self.client.get(url)

              self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

       
class ProfileUpdateTests(APITestCase):

    def setUp(self):
        self.user = UserFactory()

        refresh = CustomTokenObtainPairSerializer.get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        self.url = reverse("profile", kwargs={'version': 'v1'})

    def test_update_name_successful(self):
        response = self.client.patch(self.url, {"first_name": "New" , "last_name": "Name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "New")
        self.assertEqual(self.user.last_name, "Name")

    def test_update_email_invalid_format_fails(self):
        old_email = self.user.email

        response = self.client.patch(self.url,{'email': "hacker@test.com"})

        self.assertEqual(response.status_code,status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email,old_email)


    def test_profile_update_requires_auth(self):

        self.client.credentials()

        response = self.client.patch(self.url, {"full_name": "Hack"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
