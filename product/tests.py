from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Category, Product, ProductImages,ProductVariant,Review
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


User = get_user_model

class ProductModelTests(TestCase):
       def test_product_str(self):
              """Test the product string represetnation"""            
              category = Category.objects.create(name="Mobiles",slug= 'mobiles')
              product = Product.objects.create(
                     category = category,
                     name = 'One Plus 15',
                     slug = 'one_plus_15',
                     price = 700000.00,
                     stock = 100
              )
              self.assertEqual(str(product),'One Plus 15')
       
       def test_duplicate_slug_fails(self):
              """Test that duplicate slugs are not allowed"""       
              category = Category.objects.create(name = "Tech", slug = "tech")
              product = Product.objects.create(category= category, name = "P1", slug = "same",price = 10, stock = 1)

              with self.assertRaises(IntegrityError): # what is with and what is assertRaises and IntegrityError do
                     Product.objects.create(category=category, name = 'P2', slug = 'same', price = 20, stock = 32)
              
       
class ProductAPITests(APITestCase):
       def setUp(self):
              self.category = Category.objects.create(name = 'Mobiles', slug = 'mobiles')       
              self.product = Product.objects.create(
                     category = self.category,
                     name = "One Plus 15",
                     slug = "one_plus_15",
                     price = 700000,
                     stock = 200
              )
              
              self.product_variant = ProductVariant.objects.create(
                     product = self.product,
                     size = '256gb',
                     color = 'black',
                     price_adjustment = 60000,
                     stock = 10,
                     is_active = True
              )
              self.reveiew = Review.objects.create(
                     product = self.product,
                     user = get_user_model().objects.create_user(email = 'user2example@gamil.com', password = 'user2@1234'),
                     rating = 8,
                     comment = 'Nice product'
              )
              self.reivew_url = reverse('reviews-list', kwargs={'version': 'v1'})
              self.list_url = reverse('products-list', kwargs={'version': 'v1'})
              self.variant_list_url = reverse('variants-list', kwargs={'version': 'v1'})
              self.user = get_user_model().objects.create_user(email='user1example@gmail.com', password='password123',is_staff=True, is_superuser = True)
              self.client.force_authenticate(user=self.user)
              
              
       def test_list_products_successful(self):
              """Test that anyone can view the product list"""
              response = self.client.get(self.list_url)
              self.assertEqual(response.status_code, status.HTTP_200_OK)
              self.assertEqual(len(response.data['results']),1)
              self.assertEqual(response.data['results'][0]['name'],"One Plus 15")
              
              
       def test_list_products_edge_case(self):
              Product.objects.create(
                     category = self.category,
                     name = "Samsung Galaxy",
                     slug  = "samsung_galaxy",
                     price = 60000,
                     stock = 50
              )
              response = self.client.get(self.list_url + '?search=One Plus') # who does this goning to work the serach condition 

              self.assertEqual(len(response.data['results']),1)
              self.assertNotEqual(response.data['results'][0]['name'],"Samsung Galaxy") # why we are using result and name in here and
              
       def test_image_upload(self):
              small_gif = (
              b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
              b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
              b'\x02\x4c\x01\x00\x3b'
              )
              image = SimpleUploadedFile(name='test.gif', content=small_gif, content_type='image/gif')
              product = {
                     'name' : 'One plus 15',
                     'price' : 700000,
                     'stock' : 30,
                     'category_id' : self.category.id,
                     'uploaded_images': [image],
                     'description': 'This is a test description',
              }
              self.client.force_authenticate(user=self.user)
              response = self.client.post(self.list_url,product,format='multipart')
              self.assertEqual(response.status_code, status.HTTP_201_CREATED)
              self.assertEqual(ProductImages.objects.count(),1)
       
       def test_upload_invalid_file_type(self):
              # Create a text file but tell Django it's an image
              image = SimpleUploadedFile(
              name='not_an_image.jpg', 
              content=b'this is plain text, not a photo', 
              content_type='image/jpeg'
              )
              product = {
                     'name' : 'One plus 15',
                     'price' : 700000,
                     'stock' : 30,
                     'category_id' : self.category.id,
                     'uploaded_images': [image],
                     'description': 'This is a test description',
              }
              response = self.client.post(self.list_url,product,format = 'multipart')
              self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
              errors = str(response.data['uploaded_images'])
              self.assertIn("Upload a valid image",errors)
       
       def test_create_products_invalid_category(self):
              product = {
                     'name' : 'One plus 15',
                     'price' : 700000,
                     'stock' : 30,
                     'category_id' : 1000,
                     'description': 'This is a test description',
              }
              response = self.client.post(self.list_url,product,format='json')   

              self.assertEqual(response.status_code,status.HTTP_400_BAD_REQUEST)
              self.assertIn('Invalid pk "1000" - object does not exist.', str(response.data['category_id']))
       
       def test_list_variants_successful(self):
              response = self.client.get(self.variant_list_url)
              self.assertEqual(response.status_code, status.HTTP_200_OK)
              self.assertEqual(response.data['results'][0]['price_adjustment'],'60000.00')
       
       def test_list_variants_of_nonexistent_products(self):

              response = self.client.get(self.variant_list_url + '?product=9999')
              self.assertEqual(response.status_code, status.HTTP_200_OK)
              self.assertEqual(len(response.data['results']),0)
              
       def test_public_usr_can_see_reviews(self):
              self.client.logout()
              response = self.client.get(self.reivew_url)
              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(len(response.data['results']),1)

       def test_list_reviews_nonexistent_product(self):#edge case
              response = self.client.get(self.reivew_url + '?product_id=999')
              self.assertEqual(response.status_code,status.HTTP_200_OK)
              self.assertEqual(len(response.data['results']),0)

              