from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import override_settings


@override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_CLASSES': [], 'DEFAULT_THROTTLE_RATES': {}})

class LoginAPITests(APITestCase):
       def setUp(self):

              self.url_login = reverse('token_obtain_pair', kwargs={'version': 'v1'})
              self.url_logout  = reverse('logout', kwargs={'version': 'v1'})

       def test_login(self):
              url = reverse('token_obtain_pair', kwargs={'version': 'v1'})
              email = 'Userexample@gmail.com'
              password = 'anil@11032003'
       
              get_user_model().objects.create_user(
                     email=email,
                     password=password
              )
              data = {
                     'email' : email,
                     'password': password
                     
              }
              response = self.client.post(url,data,format='json')
              
              self.assertEqual(response.status_code, status.HTTP_200_OK)

              self.assertIn('access',response.data)
              self.assertIn('refresh',response.data)       
       
       def test_for_login_edge_case(self):
              url = reverse("token_obtain_pair", kwargs={'version': 'v1'})
              email = 'User1example@gmail.com'
              password = 'User4321Example'

              get_user_model().objects.create_user(
                     email = email,
                     password=password
              )
              data = {
                     'email': 'User2example@gmail.com',
                     'password': 'User4321Example'
              }
              
              response = self.client.post(url,data,format='json')

              self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)

              self.assertNotIn('access',response.data)
              self.assertNotIn('refresh',response.data)

       def test_logout_successful(self):
              email = 'user2@gmail.com'
              password = 'user#12342.com'

              user = get_user_model().objects.create_user(
                     email=email,
                     password=password
              )
              refresh_token = RefreshToken.for_user(user)
              url = reverse('logout', kwargs={'version': 'v1'})
              access_token = str(refresh_token.access_token)
              
              # 2. Set the ID card in the Header
              self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
              
              response = self.client.post(url,{'refresh':str(refresh_token)},format='json')
              self.assertEqual(response.status_code,status.HTTP_205_RESET_CONTENT)
       
       def test_logout_with_invaild_token_fails(self):
              email = 'user2@gmail.com'
              password = 'user#12342.com'

              user = get_user_model().objects.create_user(
                     email=email,
                     password=password
              )
              refresh_token = RefreshToken.for_user(user)
              url = reverse('logout', kwargs={'version': 'v1'})
              access_token = str(refresh_token.access_token)
              self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
              response = self.client.post(url,{'refresh': 'fake_toekn_232'},format = 'json')

              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
       
       def test_login_with_email_case_insensitive(self):

              user = get_user_model().objects.create_user(email= 'anil@gmail.com',password='anil@11032003')

              data = {
                     'email' : 'ANIL@gmail.com',
                     'password' : 'anil@11032003'
              }
              
              response = self.client.post(self.url_login, data, format = 'json')

              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertIn('access',response.data)
              self.assertIn('refresh',response.data)
       
       def test_login_with_wrong_password_fails(self):
              email = 'test@gmail.com'
              password = 'hworldo202'
              
              get_user_model().objects.create_user(email = email, password = password)

              data = {
                     'email' : email,
                     'password' : 'anil@11032003'
              }
              
              response = self.client.post(self.url_login, data, format = 'json')
              self.assertEqual(response.status_code,status.HTTP_401_UNAUTHORIZED)
       
       def test_login_updates_last_login_time(self):
              email = 'testuser@gmail.com'
              password = 'helo202@2ldi'
              
              user = get_user_model().objects.create_user(email= email, password=password)

              data = {
                     'email' : email,
                     'password' : password
              }
              self.client.post(self.url_login,data,format = 'json')
              user.refresh_from_db()
              self.assertIsNotNone(user.last_login)
       
       def test_login_with_unverified_email_fails(self):

              get_user_model().objects.create_user(email = 'testemail@gmail.com', password='test#192lmaild', is_email_verified = False)
              
              data = {
                     'email':  'testemail@gmail.com',
                     'password': 'test#192lmaild',
              }
              response = self.client.post(self.url_login, data, format = 'json')

              self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
       

