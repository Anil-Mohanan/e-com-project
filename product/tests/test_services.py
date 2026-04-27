import pytest
from decimal import Decimal
from product.services.services import get_product_price, build_comparison_matrix,reserve_inventory,deduct_inventory_for_order,add_product_stock,restore_inventory_for_order,get_product_details
from product.tests.factories import ProductFactory, ProductVariantFactory,InventoryUnitFactory
from product.models import InventoryUnit,Product


@pytest.mark.django_db
class TestProductService:
       """Business logic for pricing , comparisons , details
       """
       def test_get_product_price_simple(self):
              p = ProductFactory(price = 500)
              assert float(get_product_price(p.id) == 500)

       def test_get_product_price_with_variant(self):
              p = ProductFactory(price = 1000)
              v = ProductVariantFactory(product = p, price_adjustment = 200)
              assert float(get_product_price(p.id, v.id) == 1200)

       def test_compare_limit_validation(self):
              ids = "1,2,3,4,5"

              with pytest.raises(ValueError, match = "only compare up to 4 products"):
                     
                     build_comparison_matrix(ids)

       def test_get_product_details_success(self):
              """HAPPY PATH: Retrieve basic product details"""
              
              p = ProductFactory(name="Test CPU", price=Decimal("299.99"))
              
              details = get_product_details(p.id)
              
              assert details['name'] == "Test CPU"
              assert details['price'] == Decimal("299.99")

       def test_get_product_details_nonexistent_fails(self):
              """EDGE CASE: Passing an ID that doesn't exist"""
                            
              with pytest.raises(Product.DoesNotExist):
                     get_product_details(99999)


@pytest.mark.django_db
class TestInventoryService:
       """Critical logic for stock management and locking"""
       
       def test_reserve_inventory_fails_if_insufficient(self):
              # 1. SETUP: Product with 5 in stock
              p = ProductFactory(stock=5)
              
              # 2. ACT: Try to reserve 10
              from product.services import reserve_inventory
              success = reserve_inventory(p.id, quantity=10)
              
              # 3. ASSERT: Must fail
              assert success is False
              p.refresh_from_db()
              assert p.stock == 5 # Stock shouldn't change

       def test_deduct_inventory_for_order_successful(self):
              """HAPPY PATH: Full inventory deduction flow with buld updates"""
              p = ProductFactory(name = "GTX 4080", stock = 3)
              units = InventoryUnitFactory.create_batch(3,product = p, status = 'In Stock') 
              #We use create_batch(3) to rapidly generate related data.

              # Data format required by your service: 

              items_data = [{"product_id": p.id, "quantity": 2}]

              prices = deduct_inventory_for_order(items_data)

              assert prices[p.id] == p.price

              p.refresh_from_db()
              assert p.stock == 1
              
              sold_count = InventoryUnit.objects.filter(product = p,status = 'Sold').count()
              in_stock_count = InventoryUnit.objects.filter(product = p, status = 'In Stock').count()

              assert sold_count == 2
              assert in_stock_count == 1

       def test_deduct_inventory_fails_on_granular_desync(self):
              """EDGE CASE: Product.stock is 10, but only 1 InventoryUnit exists"""

              #1 SETUP: High aggregate stock, low granular stock
              p = ProductFactory(name = "Broken Inventory Product", stock = 10)
              InventoryUnitFactory(product = p, status = "In Stock")

              items_data = [{"product_id": p.id, "quantity": 2}]

              with pytest.raises(ValueError) as excinfo:
                     deduct_inventory_for_order(items_data)

              assert 'out of stock' in str(excinfo.value)

              p.refresh_from_db()
              assert p.stock == 10

       def test_add_product_stock_syncs_granular_units(self):
              """HAPPY PATH: Adding stock through the service creates matching InventoryUnits"""
              from product.services import add_product_stock
              
              # 1. SETUP: Start with 0 stock
              p = ProductFactory(stock=0)
              
              # 2. ACT: Add 5 items
              add_product_stock(p.id, quantity=5)
              
              # 3. ASSERT: The aggregator and the granular data must match
              p.refresh_from_db()
              assert p.stock == 5
              
              from product.models import InventoryUnit
              assert InventoryUnit.objects.filter(product=p, status='In Stock').count() == 5

       def test_add_product_stock_negative_quantity_fails(self):
              """EDGE CASE: Prevent adding a negative number (which would subtract stock)"""
              
              p = ProductFactory(stock=10)
              
              # ACT: Try to "add" -5 stock
              # A senior dev service should probably raise a ValueError here
              with pytest.raises(ValueError, match="Quantity must be positive"):
                     add_product_stock(p.id, quantity=-5)
              
              # ASSERT: Stock must remain 10
              p.refresh_from_db()
              assert p.stock == 10

       def test_restore_inventory_successful(self):
              """HAPPY PATH: Restoration logic (Order Cancelled)"""
              from product.services import restore_inventory_for_order
              
              # 1. SETUP: Product at 0 stock, with 3 units marked as 'Sold'
              p = ProductFactory(stock=0)
              InventoryUnitFactory.create_batch(3, product=p, status='Sold')
              
              items_data = [{"product_id": p.id, "quantity": 2}]
              
              # 2. ACT: Restore 2 units
              restore_inventory_for_order(items_data)
              
              # 3. ASSERT
              p.refresh_from_db()
              assert p.stock == 2
              
              
              assert InventoryUnit.objects.filter(product=p, status='In Stock').count() == 2
              assert InventoryUnit.objects.filter(product=p, status='Sold').count() == 1

       def test_restore_inventory_cannot_create_phantom_stock(self):
              """EDGE CASE: Restoring more than we have 'Sold'"""
              from product.services import restore_inventory_for_order
              p = ProductFactory(stock=0)
              # We only have ONE sold unit
              InventoryUnitFactory(product=p, status='Sold')
              
              # BUT we try to restore TWO
              items_data = [{"product_id": p.id, "quantity": 2}]
              
              # ACT
              restore_inventory_for_order(items_data)
              
              # ASSERT: Product stock should only be 1 (not 2!)
              p.refresh_from_db()
              # If your code is buggy, this next line will FAIL:
              assert p.stock == 1 

@pytest.mark.django_db
class TestReviewService:
       """Logic for processing customer feedback"""
       
       def test_add_review_successful(self):
              """HAPPY PATH: Create a valid review"""
              from product.services import add_review_process
              from user_auth.tests.factories import UserFactory
              
              u = UserFactory()
              p = ProductFactory()
              
              review = add_review_process(p, u, rating=5, comment="Amazing!")
              
              assert review.rating == 5
              assert review.comment == "Amazing!"
              assert review.product == p
              assert review.user == u

       def test_prevent_duplicate_reviews(self):
              """EDGE CASE: One user, one product, one review only"""
              from product.services import add_review_process
              from user_auth.tests.factories import UserFactory
              from django.db import IntegrityError
              
              u = UserFactory()
              p = ProductFactory()
              
              # 1. Create first review
              add_review_process(p, u, rating=5, comment="First!")
              
              # 2. ACT & ASSERT: Creating second review for SAME product should CRASH the DB
              with pytest.raises(IntegrityError):
                     add_review_process(p, u, rating=1, comment="Spam review!")
