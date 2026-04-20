from rest_framework.utils import representation
from django.http import response
import pytest
from django.urls import reverse
from rest_framework import status
from product.tests.factories import ProductFactory,ProductPurchaseHistoryFactory,CategoryFactory,ProductVariantFactory

class TestPorudctListing:
       @pytest.mark.django_db
       def test_list_products_successful(self,api_client):

              ProductFactory(name = "RTX 5090")
              ProductFactory(name = "RTX 4090")

              url = reverse('products-list',kwargs={'version': 'v1'})

              response = api_client.get(url)

              assert response.status_code == status.HTTP_200_OK
              assert len(response.data['results']) == 2

       @pytest.mark.django_db
       def test_list_products_search_fliter(self,api_client):

              ProductFactory(name="Intel core i9 14th")  # Partial match (3 words)
              ProductFactory(name="Intel core i7 14th")  # Exact match (4 words)
              ProductFactory(name="AMD Ryzen 7")         # 0 matching words


              url = reverse('products-list',kwargs={'version': 'v1'})

              response = api_client.get(url + '?search=Intel core i7 14th')

              # 3. ASSERT
              results = response.data['results']

              # Postgres correctly dropped AMD Ryzen entirely because rank = 0.000
              assert len(results) == 2

              # The EXACT match (i7) MUST be ranked #1 (highest Postgres SearchRank)
              assert results[0]['name'] == "Intel core i7 14th"

              # The PARTIAL match (i9) MUST be ranked #2
              assert results[1]['name'] == "Intel core i9 14th"
       
       @pytest.mark.django_db
       def test_retrieve_product_successful(self,api_client):
              """HAPPY PATH: Viewing a single products details via slug"""
              # 1: setup 
              product = ProductFactory(name = "RTX 5090",slug = "rtx-5090")
              url = reverse('products-detail',kwargs={'version': 'v1', 'slug': product.slug})
              response = api_client.get(url)
              assert response.status_code == status.HTTP_200_OK
              assert response.data['name'] == "RTX 5090"
       
       @pytest.mark.django_db
       def test_retrive_nonexistent_product_fails(self,api_client):
              """EDGE CASE: Looking for a ghost product"""
              url  = reverse('products-detail',kwargs={'version': 'v1','slug': 'ghost-gpu-999'})
              response = api_client.get(url)

              assert response.status_code == status.HTTP_404_NOT_FOUND

       @pytest.mark.django_db
       def test_compare_products_successful(self,api_client):
              """HAPPY PAHT: Compoare two valid products"""
              # 1. SETUP : create two products
              p1 = ProductFactory(name = "Intel i7")
              p2 = ProductFactory(name = 'Intel i9')

              # Construct the URL with a comma-separted list of IDS

              url = reverse('products-compare',kwargs = {'version':'v1'})
              query_params = f"?ids={p1.id},{p2.id}"
              response = api_client.get(url + query_params)
              
              assert response.status_code == status.HTTP_200_OK
              assert "Comparsion Successfull" in str(response.data)

              assert str(p1.id) in str(response.data)
              assert str(p2.id) in str(response.data)
       @pytest.mark.django_db
       def test_compare_products_missing_ids_fails(self, api_client):
              """EDGE CASE: Forgetting to provide any IDs"""
              url = reverse('products-compare', kwargs={'version': 'v1'})
              
              # 2. ACT: Send request without ?ids=
              response = api_client.get(url)
              
              # 3. ASSERT
              assert response.status_code == status.HTTP_400_BAD_REQUEST
              assert "Please provide product IDs" in str(response.data)

       @pytest.mark.django_db
       def test_instant_search_successful(self, api_client):
              """HAPPY PATH: Quick search results for type-ahead"""
              # 1. SETUP
              ProductFactory(name="Mechanical Keyboard")
              
              # The URL name for @action(detail=False) is usually 'basename-method_name'
              url = reverse('products-instant-search', kwargs={'version': 'v1'})
              
              # 2. ACT: Look for "Key"
              response = api_client.get(url + "?q=Key")
              
              # 3. ASSERT
              assert response.status_code == status.HTTP_200_OK
              assert "Search complete" in str(response.data)
              # We expect the keyword to match
              assert "Mechanical Keyboard" in str(response.data)
       
       @pytest.mark.django_db
       def test_instant_search_empty_query_returns_nothing(self, api_client):
              """EDGE CASE: User starts typing but submits early/empty"""
              url = reverse('products-instant-search', kwargs={'version': 'v1'})
              
              # ACT: Send empty query
              response = api_client.get(url + "?q=")
              
              # ASSERT: Check if your logic returns an empty list
              assert response.status_code == status.HTTP_200_OK
              assert response.data['data'] == [] 

       @pytest.mark.django_db
       def test_instant_search_no_results(self, api_client):
              """EDGE CASE: Searching for something that definitely isn't there"""
              url = reverse('products-instant-search', kwargs={'version': 'v1'})
              
              # ACT: Target a fake brand
              response = api_client.get(url + "?q=NonExistentBrand")
              
              # ASSERT
              assert response.status_code == status.HTTP_200_OK
              assert response.data['data'] == []

class TestProductReviwes:
       @pytest.mark.django_db
       def test_user_cannot_review_unpurchased_product(self,logged_in_client):
              """EDGE CASE: stop fake reviews from peoeple who didn't buy the item"""

              # 1: Setup:- create a product.notice the user never bought it.

              product = ProductFactory(name = "16GB DDR 5 RAM")

              # DRF action URL's are usually 'basename-action_name' with hyphens
              url = reverse('products-add-review',kwargs={'version': 'v1','slug': product.slug})

              # 2.ACT : Attempt to cheat the system and leave a 5-start review

              response = logged_in_client['client'].post(url,{"rating":5,"comment": "Good Wroking"})

              assert response.status_code == status.HTTP_400_BAD_REQUEST
              assert "You can only reiview products you have purchased" in str(response.data)

       @pytest.mark.django_db
       def test_user_can_review_purchased_product(self,logged_in_client):
              """HAPPY PATH: Letting a verified buyer leave a review"""
              # 1 Setup : create a product and getting the user from fixutre
              product = ProductFactory(name= "16GB DDR5 RAM")
              user = logged_in_client['user']

              ProductPurchaseHistoryFactory(user_id = user.id, product = product)
              url = reverse('products-add-review',kwargs={'version': 'v1', 'slug': product.slug })

              response = logged_in_client['client'].post(url,{'rating': 5, 'comment': 'Amazing!'})

              assert response.status_code == status.HTTP_201_CREATED
       

class TestCategoryAPI:
       @pytest.mark.django_db
       def test_list_categories_public(self,api_client):
              """Anyone should be able to see the cateogory tree"""

              CategoryFactory(name = "Laptops")
              
              url = reverse('category-list',kwargs={'version': 'v1'})

              response = api_client.get(url)

              assert response.status_code == status.HTTP_200_OK
              assert len(response.data)  >= 1

       @pytest.mark.django_db
       def test_non_admin_cannot_create_category(self,logged_in_client):
              """SECURITY EDGE CASE: Enusre normal users get blocker (403)"""

              url = reverse('category-list',kwargs={'version':'v1'})

              response = logged_in_client['client'].post(url,{"name": "Hacker Categories"})

              assert response.status_code == status.HTTP_403_FORBIDDEN

class TestReviewAPI:
       @pytest.mark.django_db
       def test_direct_post_to_reviews_is_disabled(self, logged_in_client):
              """GUARD RAIL: Making sure reviews only come through the approved channel"""
              url = reverse('reviews-list', kwargs={'version': 'v1'})
              
              # This should fail because 'post' is not in http_method_names
              response = logged_in_client['client'].post(url, {"rating": 5})
              
              assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

       @pytest.mark.django_db
       def test_user_cannot_edit_others_review(self, logged_in_client):
              """SECURITY EDGE CASE: User A tries to hijack User B's review"""
              from user_auth.tests.factories import UserFactory
              from product.tests.factories import ReviewFactory, ProductFactory
              
              # 1. SETUP: Create two users and a review by User B
              user_b = UserFactory(email="user_b@example.com")
              product = ProductFactory()
              review = ReviewFactory(user=user_b, product=product, comment="User B's original review")
              
              # 2. ACT: Logged-in user (User A) tries to PUT/Edit User B's review
              url = reverse('reviews-detail', kwargs={'version': 'v1', 'pk': review.id})
              response = logged_in_client['client'].put(url, {"comment": "I am User A and I changed this!", "rating": 1})
              
              # 3. ASSERT: Must be forbidden
              assert response.status_code == status.HTTP_403_FORBIDDEN
              # Verify the comment didn't actually change in the DB
              review.refresh_from_db()
              assert review.comment == "User B's original review"


class TestProductVariantAPI:
       @pytest.mark.django_db
       def test_list_variants_public_success(self,api_client):
              """HAPPY PATH : Guests can see variants (Verified Read-Only)"""
              ProductVariantFactory()

              # URL name from urls.py basename = 'variants'
              url = reverse('variants-list',kwargs={'version':'v1'})
              response = api_client.get(url)
              assert response.status_code == status.HTTP_200_OK
              assert len(response.data) >= 1

       @pytest.mark.django_db
       def test_filter_variants_by_products(self,api_client):
              """EDGE CASE: Prove that filtering by product ID works"""

              p1 = ProductFactory(name = "Laptop A")
              p2 = ProductFactory(name = "Laptop B")

              v1 = ProductVariantFactory(product = p1)
              v2 = ProductVariantFactory(product = p2)

              url =  reverse('variants-list',kwargs={'version': 'v1'})

              response = api_client.get(url + f"?product={p1.id}")

              assert response.status_code == status.HTTP_200_OK
              assert len(response.data['results']) == 1
              assert response.data['results'][0]['id'] == v1.id
       
       @pytest.mark.django_db
       def test_variant_filter_with_nonexistent_product(self, api_client):
              """EDGE CASE: Filtering by a ghost product ID"""
              url = reverse('variants-list', kwargs={'version': 'v1'})
              response = api_client.get(url + "?product=999999")
              
              assert response.status_code == status.HTTP_200_OK
              assert len(response.data['results']) == 0
