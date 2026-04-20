import io
import pytest
import pytest
from PIL import Image
from product.models import ProductImages
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from product.tests.factories import (
       ProductFactory,
       ProductVariantFactory,
       CategoryFactory,
       ReviewFactory,
       InventoryUnitFactory,
       ProductPurchaseHistoryFactory
)



@pytest.mark.django_db
def test_product_str():

       product = ProductFactory(name = "RTX 5090")
       assert str(product) == "RTX 5090"

@pytest.mark.django_db
def test_duplicate_slug_fails():
       category = CategoryFactory(name = "GPU")

       # 1 Create the first product with a specific test_duplicate_slug_fails

       ProductFactory(category=category,name= 'P1',slug = "same")
       # 2: Attempt to create a second prodcut with the exact same test_duplicate_slug_fails

       # wrap it in pytest.raise to tell Pytest: "Expect a databse crash here"
       with pytest.raises(ValidationError):
              ProductFactory(category = category , name= "p2", slug = "same")

@pytest.mark.django_db
def test_category_creation():
       category = CategoryFactory(name = "Laptops")
       assert str(category) == "Laptops"

@pytest.mark.django_db
def test_product_variant_str():
       variant = ProductVariantFactory(
              color= "Black",
              attribute_name = "RAM",
              attribute_value = "16GB"
       )
       assert "Black" in str(variant)
       assert "16GB" in str(variant)


@pytest.mark.django_db
def test_inventory_unit_creation():
       unit  = InventoryUnitFactory(
              serial_number = "SN-X1234",
              status = "In Stock"
       )
       assert "SN-X1234" in str(unit)
       assert "In Stock" in str(unit)

@pytest.mark.django_db
def test_review_creation():
       review = ReviewFactory(rating = 5)
       assert "5 Star" in str(review)

@pytest.mark.django_db
def test_purchase_history_unique_together():
       # Create the first purchase
       history = ProductPurchaseHistoryFactory()
       
       # Attempt to create a duplicate purchase record for the exact same user & product
       # Because we didn't override full_clean() on this model, it WILL hit the 
       # Database level constraint and raise IntegrityError.
       with pytest.raises(IntegrityError):
              ProductPurchaseHistoryFactory(user_id=history.user_id, product=history.product)


@pytest.mark.django_db
def test_product_missing_requrired_specifications_fails():
       # 1: Setup : Create a category that absolutely Demands "CPU", and "RAM"

       category = CategoryFactory(
              name = "Laptops",
              required_specs_keys = ["CPU", "RAM"]
       )

       with pytest.raises(ValidationError) as exc_info:
              
              ProductFactory(
                     category=category, 
                     name="MacBook", 
                     specifications={"CPU": "M1"} # Missing RAM!
              )
       assert "missing required specifications: RAM" in str(exc_info.value)

@pytest.mark.django_db
def test_category_and_product_auto_generate_slugs():
       category = CategoryFactory(name="Gaming Laptops", slug="")
       product = ProductFactory(category=category, name="RTX 5090 Super", slug="")

       assert category.slug == "gaming-laptops"
       assert product.slug == "rtx-5090-super"

@pytest.mark.django_db
def test_product_image_resizes_large_images():
       # 1. SETUP: We need a product to attach the image to
       product = ProductFactory(name="Camera")
       
       # Create a massive 2000x2000 Image entirely in RAM using Pillow
       heavy_image = Image.new('RGB', (2000, 2000), color='red')
       byte_stream = io.BytesIO()
       heavy_image.save(byte_stream, format='PNG') # Intentionally save it as PNG
       
       # Convert the RAM byte stream into a format Django understands
       django_file = ContentFile(byte_stream.getvalue(), name='heavy_unoptimized.png')
       
       # 2. ACT: Save the beast to the database (This triggers line 67 in models.py)
       product_image = ProductImages.objects.create(
              product=product,
              image=django_file
       )
       
       # 3. ASSERT: Open the officially saved file from the storage system
       saved_img = Image.open(product_image.image)
       
       # Did your code crush it down?
       assert saved_img.width == 800
       assert saved_img.height == 800
       
       # Did your code forcefully convert the PNG to a highly optimized JPEG?
       assert saved_img.format == 'JPEG'
