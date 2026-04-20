from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError



@override_settings(REST_FRAMEWORK={'DEFAULT_THROTTLE_CLASSES': [], 'DEFAULT_THROTTLE_RATES': {}})
class UserModelTests(TestCase):
       
       def test_create_user_with_valid_email_and_password(self):
              """Test Creating a new User with an email is successful"""
              email = 'test@example.com'
              password = 'StrongTestPass@1234'

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
              password = 'StrongTestPass@1234'

              user = get_user_model().objects.create_user( #ARRANGE
                     email = email,
                     password = password
              )
              user.refresh_from_db()
              self.assertFalse(user.is_email_verified) #ASSERT
              self.assertIs(user.is_email_verified,False)
              user2 = get_user_model().objects.create_user(email='v@ex.com',password='StrongTestPass@1234',is_email_verified = True)
              self.assertTrue(user2.is_email_verified)

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
                     get_user_model().objects.create_user(email=None, password='StrongTestPass@1234')
       
       def test_email_is_normalized_to_lowercase(self):
              user1 = get_user_model().objects.create_user(email="ANIL1@gmail.com",password='StrongTestPass@1234')
              user1.refresh_from_db()
              self.assertEqual(user1.email,'anil1@gmail.com')
      
       def test_password_is_hashed_not_plaintext(self):
              user = get_user_model().objects.create_user(email='test@gmail.com',password='StrongTestPass@1234')
              user.refresh_from_db()
              self.assertNotEqual(user.password,'StrongTestPass@1234')
              self.assertTrue(user.check_password('StrongTestPass@1234'))
       
       def test_user_str_method(self):
               user = get_user_model().objects.create_user(email='test@gmail.com',password='StrongTestPass@1234')
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
