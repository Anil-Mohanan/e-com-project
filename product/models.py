from django.db.models.fields import return_None
from enum import unique
from django.db import models
from django.utils.text import slugify
from user_auth.models import User
from django.core.validators import FileExtensionValidator
from PIL import Image
import io
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

def validate_image_size(value): # Custom validator to check uploaded image file size boundaries
       limit_mb = 2.0 # Set the size limit threshold to 2.0 Megabytes
       limit_bytes = limit_mb * 1024 * 1024 # Convert 2MB to bytes (2.0 * 1048576 = 2097152 bytes)
       if value.size > limit_bytes: # Check if the uploaded file's size exceeds the 2MB limit
              raise ValidationError(f"Image size cannot exceed {limit_mb}MB.") # Raise validation error to block saving and show error in admin panel

#Category model
class Category(models.Model):
       name = models.CharField(max_length=100)
       slug = models.SlugField(unique=True, blank=True,max_length=255)# 
       image = models.ImageField(upload_to='category_images/',blank=True, null= True, validators=[FileExtensionValidator(['jpg','jpeg','png','webp']),validate_image_size])
       required_specs_keys = models.JSONField(default = list, blank= True)
       metadata = models.JSONField(default = dict, blank=True, help_text = "Flexible field for UI data like video_url")
       class Meta:
              verbose_name_plural = "Categories"
              ordering = ['name']
       def save(self, *args, **kwargs):
              #Auto-generate slug if empty(eg., "Smart Phone" -> "smart-phones")
              if not self.slug:
                     self.slug = slugify(self.name)
              super().save(*args,**kwargs)
              
       def __str__(self):
              return self.name
#Product Model

class Product(models.Model):
       category = models.ForeignKey(Category,related_name='products',on_delete=models.CASCADE)
       name = models.CharField(max_length=200,db_index=True)
       brand = models.CharField(max_length=100, blank=True, null=True,db_index=True)
       slug = models.SlugField(unique=True,blank=True,max_length=255)
       description = models.TextField()
       price = models.DecimalField(max_digits=10, decimal_places=2)
       stock = models.PositiveIntegerField()
       is_active = models.BooleanField(default=True,db_index=True)
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)
       specifications = models.JSONField(default=dict, blank= True)
       base_attribute_name = models.CharField(
              max_length = 100,
              blank = True,
              null = True,
              help_text = "Optional: Name of the base confiuration(eg. ,'Ram', or 'VRAM')"
       )
       base_attribute_value = models.CharField(
              max_length = 100,
              blank = True,
              null = True,
              help_text = "Optional: Value of the base confiuration (e.g,'16Gb' or '128GB SSD')"
       )
       seller = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)


       def save(self,*args,**kwargs):
              self.full_clean()
              if not self.slug:
                     self.slug = slugify(self.name)
              super().save(*args,**kwargs)
       
       def clean(self):

              if self.category and self.category.required_specs_keys:
                     for key in self.category.required_specs_keys:
                            if key not in self.specifications:
                                   raise ValidationError(f"missing required specifications: {key} for category {self.category.name}")

                     
       def __str__(self):
              return self.name

class Color(models.Model):
       name = models.CharField(max_length = 100, unique = True)# for human redable name
       hex_code = models.CharField(max_length=7, default="#FFFFFF", help_text="CSS hex code for frontend swatch (e.g., #2563eb)")

       def __str__(self):
              
              return self.name


#Product Images (One Product -> Many Images)
class ProductImages(models.Model):
       product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
       variant = models.ForeignKey('ProductVariant', related_name='variant_images',on_delete=models.CASCADE,null=True, blank = True)
       color = models.ForeignKey('Color', on_delete=models.SET_NULL, null=True, blank=True, related_name='product_images') 
       is_primary = models.BooleanField(default=False)
       image = models.ImageField(upload_to='product_images/', validators=[FileExtensionValidator(['jpg','jpeg','png','webp'])])
       is_thumbnail = models.BooleanField(default=False)
       is_primary = models.BooleanField(default=False)
       MAX_IMAGE_SIZE = (800, 800)
       JPEG_QUALITY = 70# Which image show on the list page ?
       def save(self, *args, **kwargs):
              if self.image and hasattr(self.image, 'file'):
                     from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
                     if isinstance(self.image.file, (InMemoryUploadedFile, TemporaryUploadedFile)):
                            img = Image.open(self.image)
                            img = img.convert('RGB')
                            if img.width > 800 or img.height > 800:
                                   img.thumbnail(self.MAX_IMAGE_SIZE)
                            output = io.BytesIO()
                            img.save(output, format='JPEG', quality=self.JPEG_QUALITY)
                            output.seek(0)
                            self.image = ContentFile(output.getvalue(), name=self.image.name)
              super().save(*args, **kwargs)


       def __str__(self):
              return f"Image for {self.product.name}"


class ProductVariant(models.Model):
       product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
       sku = models.CharField(max_length=100, unique=True, null=True, blank=True)

       color = models.ForeignKey('Color', on_delete=models.PROTECT, null=True, blank=True)

       attributes = models.JSONField(default=dict, help_text="Stores varying specs like {'RAM': '16GB', 'Storage': '512GB'}")

       description = models.TextField(
              blank = True,
              null = True,
              help_text = "Optional:Technical specs or details sepcific to This Varaint"
       )
       
       price = models.DecimalField(max_digits=10, decimal_places = 2, help_text = "Total price for THIS variant")
       
       stock = models.PositiveIntegerField(default=0) # Each variant have different stock
       
       is_active = models.BooleanField(default=True)
       def __str__(self):
              return f"{self.product.name} - SKU: {self.sku}"

class InventoryUnit(models.Model):

       STATUS_CHOICES =  (
              ('In Stock','In Stock'),# The first value in the inner tuple is what gets saved to the database (e.g. 'In Stock'). The second value is what gets displayed to humans in the Django Admin interface or dropdown menus
              ('Reserved','Reserved'),
              ('Sold','Sold'),
              ('Returned','Returned'),
       )

       product = models.ForeignKey(Product,related_name='inventory_units',on_delete=models.CASCADE)
       variant = models.ForeignKey(ProductVariant,related_name='inventory_units',on_delete=models.CASCADE,null=True,blank=True)
       color = models.ForeignKey('Color',on_delete=models.SET_NULL,null = True, blank =True, related_name='inventory_units')
       serial_number = models.CharField(max_length=100,unique=True,db_index=True) # db_index = True make the serial_number index 
       status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='In Stock',db_index=True)
       current_order_id = models.UUIDField(null = True, blank = True, db_index = True)
       date_added = models.DateTimeField(auto_now_add=True)

       def __str__(self):
              return f"{self.product.name} - S/N: {self.serial_number} ({self.status})"


class Review(models.Model):
       product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name= 'reviews')              
       user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
       rating = models.IntegerField(default=0)
       comment = models.TextField(default="",blank=True, null=True)
       created_at  = models.DateTimeField(auto_now_add=True)

       def __str__(self):
              return f"{self.user.first_name} - {self.product.name} ({self.rating} Stars)"
       
       class Meta:
              unique_together = [['product', 'user']]
              

class ProductPurchaseHistory(models.Model):
       user_id = models.IntegerField(db_index=True)
       product = models.ForeignKey(Product,on_delete=models.CASCADE)       
       purchased_at = models.DateField(auto_now_add=True)

       class Meta:
              unique_together = [['user_id','product']]



class ProductBehaviorLog(models.Model):
       """Stores raw user interaction events for the behavior analytics engine.
              user_id is IntegerField (not FK) so that Store None for not logged in users
       """
       EVENT_CHOICES = (
              ('product.viewed','Product Viewed'), # User Opened a Product Detail page
              ('product.searched','Product Searched'),# User ran a search query
              ('product.added_to_cart','Product Added To Cart'), #User put Product in their cart
       )

       event_type = models.CharField(max_length = 50,choices = EVENT_CHOICES, db_index = True) # db_index true becuase analytics will GROUP By envet_type constantily

       product_id = models.IntegerField(null = True, blank = True, db_index = True) # null_true Becasue search events have no single Product

       user_id = models.IntegerField(null = True, blank = True, db_index = True)
       #null for anonymous (not logged in) users

       session_key = models.CharField(max_length = 40, null = True, blank = True)# browser session ID to track anonymous behaviro
       
       metadata = models.JSONField(default = dict, blank = True) # Flexible: stores search query, quantity added , etc.

       created_at = models.DateTimeField(auto_now_add=True,db_index = True) # Indexed for time-range analytics (e.g, trending this week)

       class Meta:
              indexes = [
                     # Compound index: "All views for product X in date range" - one fast query
                     models.Index(fields=['product_id','event_type','created_at']),
              ]
       
       def __str__(self):
              return f"{self.event_type} | product = {self.product_id} | user = {self.user_id}"




class ProductRecommendation(models.Model):
       """
       Pre-computed 'Customers also viewed recommendation. 
       Written nightly Celery Beat. Read instantly by the API.
       This table is the performance layer - instead of querying millions of 
       behavior log rows on every request, serving one fast lookup.       
       """

       source_product = models.ForeignKey(
              Product,
              on_delete=models.CASCADE,
              related_name='recommendations',
       )# the product the user is currently viewing 

       recommended_product = models.ForeignKey(
              Product,
              on_delete=models.CASCADE,
              related_name = 'recommended_in',
       )# The product suggested along side iter

       score = models.FloatField(default=0.0) # the socre of how well the recommondation is

       computed_at = models.DateTimeField(auto_now=True)

       class Meta:
              unique_together = [['source_product', 'recommended_product']]
              # prevents duplicate pairs. if the task runs twice , it updates

              ordering = ['-score']
              # Higest score recommedation first.

       def __str__(self):
              return f"{self.source_product.name} -> {self.recommended_product.name} (score: {self.score})"
              

