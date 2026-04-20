from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings


@override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_CLASSES': [], 'DEFAULT_THROTTLE_RATES': {}})

class DeleteAccountAPITests(APITestCase):
       def test_delete_account_successful(self):
              """Test that a logged-in user can delete their account"""

              email = 'user2@gmail.com'
              password = 'user#12342.com'

              user = get_user_model().objects.create_user(
                     email=email,
                     password=password
              )
              refresh_token = RefreshToken.for_user(user)
              self.client.credentials(HTTP_AUTHORIZATION = f'Bearer {refresh_token.access_token}')
              
              url = reverse('delete_account', kwargs={'version': 'v1'})
              response = self.client.delete(url)

              self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
              self.assertFalse(get_user_model().objects.filter(email = email).exists())
              
       def test_delete_account_successful_edge_case(self):
              email = 'user2@gmail.com'
              password = 'user#12342.com'

              get_user_model().objects.create_user(
                     email=email,
                     password=password
              )
              self.client.credentials()
              
              url = reverse('delete_account', kwargs={'version': 'v1'})
              response = self.client.delete(url)

              self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
              self.assertTrue(get_user_model().objects.filter(email=email).exists)

class EmailVerificationTests(APITestCase):
       def test_email_verification_successful(self):
              email = 'user2@gmail.com'
              password = 'user#12342.com'

              user = get_user_model().objects.create_user(
                     email=email,
                     password=password
              )
              self.assertFalse(user.is_email_verified)

              uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
              token = default_token_generator.make_token(user)

              url = reverse('verify_email', kwargs={'version': 'v1', 'uidb64':uidb64,'token': token})
              response = self.client.get(url)

              user.refresh_from_db()
              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertTrue(user.is_email_verified)
       def test_email_verification_with_invalid_token_fails(self):
              email = 'user2@gmail.com'
              password = 'user#12342.com'

              user = get_user_model().objects.create_user(
                     email=email,
                     password=password
              ) 
              uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

              url = reverse('verify_email', kwargs={'version': 'v1', 'uidb64': uidb64, 'token' : 'This is fake token'})
              response = self.client.get(url)

              user.refresh_from_db()
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
              self.assertFalse(user.is_email_verified)


