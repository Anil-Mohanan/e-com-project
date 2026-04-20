from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.core import mail


@override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_CLASSES': [], 'DEFAULT_THROTTLE_RATES': {}})

class RegistrationAPITest(APITestCase):
       
       def setUp(self):

              self.url = reverse('register', kwargs={'version': 'v1'})
       
       def test_registration_successful(self): 
              """Test that a user can regsiter via the API"""
              url = reverse('register', kwargs={'version': 'v1'}) # What is 'reverse'
              data = {
                     'email': 'newuser@example.com',
                     'password': 'pas@1989',
                     'full_name': 'Test User'
              }
              
              response = self.client.post(url,data,format='json')

              self.assertEqual(response.status_code,status.HTTP_201_CREATED)# what is this 'assertEqual'
              
       def test_registration_with_same_email(self): # Edge Case
              """Testing that a User cannot Use same email again for regsiter"""
              url = reverse('register', kwargs={'version': 'v1'})
              email = 'duplicate@example.com'

              get_user_model().objects.create_user(
                     email=email,
                     password="OrginalPassword123"
              )
              
              data = {
                     'email': email,
                     'password': 'NewPassword123',
                     'full_name': 'Test User'
              }

              response = self.client.post(url,data,format='json') 
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
              
       def test_registration_returns_user_data_without_password(self):
              email = 'anil@342gmail.com'
              data = {
                     'email': email,
                     'password' : 'anil#11032003',
              }
              url = reverse('register', kwargs={'version': 'v1'})
              response = self.client.post(url,data,format = 'json')
              self.assertIn(response.data['email'],email)
              self.assertNotIn('password',response.data)
       
       def test_registration_sends_verification_email(self):
              url = reverse('register', kwargs={'version': 'v1'})
              data = {
                     'email' : 'mailtest@gmail.com',
                     'password' : 'pass@2143#13',
                     'full_name' : 'maintester',
              }

              self.client.post(url,data,format = 'json')
              # verify 1 email was sent
              self.assertEqual(len(mail.outbox),1)
              # Verfify the recipent is correct
              self.assertEqual(mail.outbox[0].to[0],'mailtest@gmail.com')
              
       def test_registration_with_weak_password_fails(self): # Edge Case
              data = {
                     'email' : 'testexample@gmail.com',
                     'password' : 'password123',
              }
              url = reverse('register', kwargs={'version': 'v1'})
              response = self.client.post(url,data,format= 'json')
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)

       def test_registration_with_missing_email_fails(self): #Edge Case
              url = reverse('register', kwargs={'version': 'v1'})
              data = {
                     'eamil' : None,
                     'password': 'ValidPassword1332#2134',
              }
              response = self.client.post(url,data,format = 'json')
              
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
              
       def test_registration_with_blank_fields_fails(self): # Edge Case
              url = reverse('register', kwargs={'version': 'v1'})

              data = {
                     'email' : '',
                     'password': '',
              }
              response = self.client.post(url,data,format = 'json')
              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

       def test_registration_blocks_sql_injection_input(self): # Edge Case
              url = reverse('register', kwargs={'version': 'v1'})
              
              data = {
                     'email' : ' OR 1=1; --@gmail.com',
                     'password' : 'ValidPass123!',
              }
              
              response = self.client.post(url,data,format = 'json')

              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
              
       def test_registration_blocks_xss_input(self): # Edge Case
              url = reverse('register', kwargs={'version': 'v1'})
              data = {
                     'email' : 'hacker@gmail.com',
                     'password' : 'hacker3134#1',
                     'full_name' : '<script>alert("xss")</script>',
              }
              response = self.client.post(url, data, format = 'json')
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
              
       def test_registration_requires_email_verification(self):
              data = {
                     'email' : 'testuser@gmail.com',
                     'password' : 'testuser#232193@1l',
              }
              self.client.post(self.url, data, format = 'json')
              user = get_user_model().objects.get(email = 'testuser@gmail.com')
              self.assertFalse(user.is_email_verified)
       
       def test_registration_cannot_force_email_verification(self):
              data = {
                     'email' : 'hacker353@gmail.com',
                     'password' : 'hacker332492!2',
                     'is_email_verified' : True,
              }  
              self.client.post(self.url, data, format = 'json')  
              user = get_user_model().objects.get(email= 'hacker353@gmail.com')
              self.assertFalse(user.is_email_verified)

       def test_registration_with_short_password_fails(self): # Edge Case
              data = {
                     'email' : 'anil353@gmail.com',
                     'password' : 'a',
              }
              response = self.client.post(self.url, data, format = 'json')
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
              
       def test_registration_with_invalid_email_format_fails(self): # Edge Case
              data = {
                     'email' : 'anil*2atmaildotcom',
                     'password' : 'anil#23@11032003'
              }
              response = self.client.post(self.url, data, format = 'json')
              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
              
       def test_registration_with_missing_password_fails(self):
              data = {
                     'email': 'Anil353@gmail.com'
              }
              response = self.client.post(self.url, data, format = 'json')
              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
              
       def test_registration_with_missing_email_fails(self):
              data = {
                     
                     'password': 'anil@11032003'
              }
              response = self.client.post(self.url, data, format = 'json')
              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
              
       def test_registration_with_extra_unexpected_fields_ignored(self):
              data = {
                     'email' : 'anil252@gmail.com',
                     'password' : 'anil@11032003',
                     'fake_feild' : 'something_that_is_not_what_you_think'
              }
              response = self.client.post(self.url, data, format = 'json')
              user = get_user_model().objects.get(email = 'anil252@gmail.com')
              self.assertNotIn('fake_field', response.data)
              self.assertEqual(response.status_code, status.HTTP_201_CREATED)
              
       # @override_settings(
       #  CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
       #  REST_FRAMEWORK={
       #      'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.AnonRateThrottle'],
       #      'DEFAULT_THROTTLE_RATES': {'anon': '1/min'} # Even stricter
       #  }
       # )
       # def test_registration_rate_limit_enforced(self):
       #        for i in range(4):
       #               data = {
       #               'email' : f'anil2{i}2@gmail.com',
       #               'password' : 'anil@11032003',
       #               }
       #               response = self.client.post(self.url, data, format = 'json')
       #               if i < 2:
       #                      self.assertEqual(response.status_code,status.HTTP_201_CREATED)
       #               else:
       #                      self.assertEqual(response.status_code,status.HTTP_429_TOO_MANY_REQUESTS)
              
