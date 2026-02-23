from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core import mail
from django.contrib.auth import authenticate
# Create your tests here.
@override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_CLASSES': [], 'DEFAULT_THROTTLE_RATES': {}})
class UserModelTests(TestCase):
       
       def test_create_user_with_valid_email_and_password(self):
              """Test Creating a new User with an email is successful"""
              email = 'test@example.com'
              password = 'testpassword123'

              #Act : Cretae the user
              user = get_user_model().objects.create_user(
                     email=email,
                     password=password
              )
              
              #Assert :Check if the user was Created  correntily
              self.assertEqual(user.email,email) # Check email match
              self.assertTrue(user.check_password(password))# Check password is hashed
              self.assertFalse(user.is_staff)#Normal user shoudn't be Staff
              self.assertEqual(get_user_model().objects.count(),1)
              self.assertNotEqual(user.password, password)
              self.assertTrue(user.is_active)

              
              
       def test_new_user_email_not_verified_by_default(self):
              """Test that new user is created with is_email_verified = False"""
              email = 'test@example.com'
              password = 'testpassword123'

              user = get_user_model().objects.create_user( #ARRANGE
                     email = email,
                     password = password
              )
              user.refresh_from_db()
              self.assertFalse(user.is_email_verified) #ASSERT
              self.assertIs(user.is_email_verified,False)
              user2 = get_user_model().objects.create_user(email='v@ex.com',password='p',is_email_verified = True)
              self.assertFalse(user2.is_email_verified)

       def test_create_superuser(self):
              email = 'admin@example.com'
              password='adminpassword123'
              user = get_user_model().objects.create_superuser(
                     email = email,
                     password=password
              )
              self.assertEqual(user.email,email)
              self.assertTrue(user.check_password(password))
              self.assertTrue(user.is_staff)
              self.assertTrue(user.is_superuser)
              self.assertTrue(user.is_email_verified)
              self.assertTrue(user.is_active)
              self.assertEqual(get_user_model().objects.filter(is_superuser=True).count(),1)
              
       def test_create_user_no_email_raise_error(self):
              """Test that crateing a user without an email raise a ValueError"""
              with self.assertRaises(ValueError):
                     get_user_model().objects.create_user(
                            email='',
                            password="passowrd123"
                     )
              with self.assertRaises(ValueError):
                     get_user_model().objects.create_user(email=None, password="password123")
       
       def test_email_is_normalized_to_lowercase(self):
              user1 = get_user_model().objects.create_user(email="ANIL1@gmail.com",password='ANIl123')
              user1.refresh_from_db()
              self.assertEqual(user1.email,'anil1@gmail.com')
      
       def test_password_is_hashed_not_plaintext(self):
              user = get_user_model().objects.create_user(email='test@gmail.com',password='test123')
              user.refresh_from_db()
              self.assertNotEqual(user.password,'test123')
              self.assertTrue(user.check_password('test123'))
       
       def test_user_str_method(self):
               user = get_user_model().objects.create_user(email='test@gmail.com',password='test123')
               user.refresh_from_db()
               self.assertEqual(str(user),user.email)
       
       def test_create_user_without_password_fails(self):
              
              with self.assertRaises(ValueError):
                     user = get_user_model().objects.create_user(email='nopass@gmail.com',password=None)

       def test_create_user_with_space_only_password_fails(self):#Edge case
              with self.assertRaises(ValueError):
                     get_user_model().objects.create_user(email='anil@gmail.com',password='            ')
       
       
       def test_create_user_with_short_password_fails(self):
              with self.assertRaises(ValidationError):
                     get_user_model().objects.create_user(email='anil@gmail.com',password='s')
                     
       def test_create_user_with_numeric_only_password_fails(self): # Edge Case
              with self.assertRaises(ValidationError):
                     get_user_model().objects.create_user(email='anil@gmail.com',password='11032003')
              
       def  test_create_user_with_excessively_long_password_fails(self):
              with self.assertRaises(ValueError):
                     get_user_model().objects.create_user(email='anil@gmail.com',password='a' * 200)
                     
       def test_create_user_with_weak_password_fails(self):
              with self.assertRaises(ValidationError):
                     get_user_model().objects.create_user(email='anil@gmail.com',password='password123')
       
       def test_password_too_similar_to_email_fails(self):
              with self.assertRaises(ValidationError):
                     get_user_model().objects.create_user(email='anil@gmail.com',password='anil@gmail.com')
       
       def test_create_user_with_duplicate_email_fails(self):
              user = get_user_model().objects.create_user(email = 'anil@gmail.com',password = 'Anil@11032002')       
              
              with self.assertRaises(IntegrityError):
                     get_user_model().objects.create_user(email='anil@gmail.com',password='Anil@100402006')

       def test_email_normalization_prevents_duplicates(self): # Edge Case
              user = get_user_model().objects.create_user(email = 'ANIL@GMAIL.COM',password = 'Anil@11032002')       
              
              with self.assertRaises(IntegrityError):
                     get_user_model().objects.create_user(email='anil@gmail.com',password='Anil@100402006')
                     
       def test_email_with_whitespace_is_duplicate(self): # Edge Case
              user = get_user_model().objects.create_user(email = 'anil@gmail.com',password = 'Anil@11032002')       
              
              with self.assertRaises(IntegrityError):
                     get_user_model().objects.create_user(email='   anil@gmail.com  ',password='Anil@100402006')
       
       def test_create_user_with_long_email_fails(self): #Edge Case
              with self.assertRaises(ValueError):
                     get_user_model().objects.create_user(email ='a' * 250 + '@gmail.com', password="passoe234#@1")

       def test_create_user_with_special_characters_email_valid(self):
              user = get_user_model().objects.create_user(email = 'anil.__.m@gmail.com',password='anil@11032003')
              self.assertEqual(user.email,'anil.__.m@gmail.com')

       def test_create_user_with_invalid_email_format_fails(self):
              with self.assertRaises(ValueError):
                     get_user_model().objects.create_user(email= 'anil-at-gmail.com',password='anil@11032003')
       
       # def test_full_name_optional(self):
       #        user = get_user_model().objects.create_user(email='noname@test.com', password='noneame#100203')
       #        self.assertEqual(user.get_full_name, '')
              
       # def test_full_name_max_length_validation(self):
       #        with self.assertRaises(ValueError):
       #               get_user_model().objects.create_user(email='longname@test.com', password='Password123', full_name='a' * 300)
       
       def test_default_user_is_not_superuser(self):
              user = get_user_model().objects.create_user(email= 'anil@gmail.com',password='anil@11032003')
              self.assertFalse(user.is_superuser)
       
       def test_create_superuser_has_all_permissions(self):
              user = get_user_model().objects.create_superuser(email=  'testexample@gamil.com', password='test@1234023')
              self.assertTrue(user.is_staff)
              self.assertTrue(user.is_superuser)
              
       def test_create_superuser_with_invalid_flags_fails(self):
              with self.assertRaises(ValueError):
                     get_user_model().objects.create_superuser(email='example@gmail.com',password='eamp2@1343',is_superuser = False)
              with self.assertRaises(ValueError):
                     get_user_model().objects.create_superuser(email='example@gmail.com',password='eamp2@1343',is_staff = False)
              
       
class RegistrationAPITest(APITestCase):
       
       def setUp(self):

              self.url = reverse('register')
       
       def test_registration_successful(self): 
              """Test that a user can regsiter via the API"""
              url = reverse('register') # What is 'reverse'
              data = {
                     'email': 'newuser@example.com',
                     'password': 'pas@1989',
                     'full_name': 'Test User'
              }
              
              response = self.client.post(url,data,format='json')

              self.assertEqual(response.status_code,status.HTTP_201_CREATED)# what is this 'assertEqual'
              
       def test_registration_with_same_email(self): # Edge Case
              """Testing that a User cannot Use same email again for regsiter"""
              url = reverse('register')
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
              url = reverse('register')
              response = self.client.post(url,data,format = 'json')
              self.assertIn(response.data['email'],email)
              self.assertNotIn('password',response.data)
       
       def test_registration_sends_verification_email(self):
              url = reverse('register')
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
              url = reverse('register')
              response = self.client.post(url,data,format= 'json')
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)

       def test_registration_with_missing_email_fails(self): #Edge Case
              url = reverse('register')
              data = {
                     'eamil' : None,
                     'password': 'ValidPassword1332#2134',
              }
              response = self.client.post(url,data,format = 'json')
              
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
              
       def test_registration_with_blank_fields_fails(self): # Edge Case
              url = reverse('register')

              data = {
                     'email' : '',
                     'password': '',
              }
              response = self.client.post(url,data,format = 'json')
              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

       def test_registration_blocks_sql_injection_input(self): # Edge Case
              url = reverse('register')
              
              data = {
                     'email' : ' OR 1=1; --@gmail.com',
                     'password' : 'ValidPass123!',
              }
              
              response = self.client.post(url,data,format = 'json')

              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
              
       def test_registration_blocks_xss_input(self): # Edge Case
              url = reverse('register')
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
              
class LoginAPITests(APITestCase):
       def setUp(self):

              self.url_login = reverse('token_obtain_pair')
              self.url_logout  = reverse('logout')

       def test_login(self):
              url = reverse('token_obtain_pair')
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
              url = reverse("token_obtain_pair")
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
              url = reverse('logout')
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
              url = reverse('logout')
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
              print(f"User Active: {user.is_active}, User Verified: {user.is_email_verified}")
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
       

       
              
class ProfileAPITests(APITestCase):
       def test_get_user_profile(self):
              email = 'user3example@gmail.com'
              password = 'user1234example'
             

              user = get_user_model().objects.create_user(
                     email=email,
                     password=password

              )

              refresh_token = RefreshToken.for_user(user)
              access_token = str(refresh_token.access_token)

              self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

              url = reverse('profile')
              response = self.client.get(url)

              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(response.data['email'],user.email)
       
       def test_get_user_profile_edge_case(self):
              email = 'user1exaple@gmail.com'
              password = 'user5678exapmle'

              user = get_user_model().objects.create_user(
                     email= email,
                     password=password
              )
              self.client.credentials()

              url = reverse('profile')
              response = self.client.get(url)

              self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

       
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
              
              url = reverse('delete_account')
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
              
              url = reverse('delete_account')
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

              url = reverse('verify_email',kwargs={'uidb64':uidb64,'token': token})
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

              url = reverse('verify_email',kwargs={'uidb64': uidb64, 'token' : 'This is fake token'})
              response = self.client.get(url)

              user.refresh_from_db()
              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
              self.assertFalse(user.is_email_verified)


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

        url = reverse("profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token_denied(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake.token.here")

        url = reverse("profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class ProfileUpdateTests(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="profile@test.com",
            password="Password123",
            full_name="Old Name"
        )

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        self.url = reverse("profile")

    def test_update_name_successful(self):
        response = self.client.patch(self.url, {"full_name": "New Name"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "New Name")

    def test_update_email_invalid_format_fails(self):
        response = self.client.patch(self.url, {"email": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_update_requires_auth(self):
        self.client.credentials()

        response = self.client.patch(self.url, {"full_name": "Hack"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
