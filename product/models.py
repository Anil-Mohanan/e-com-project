from django.db import models
from django.utils.text import slugify
from user_auth.models import User
from django.core.validators import FileExtensionValidator
from PIL import Image
import io
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

#Category model

class Category(models.Model):
       name = models.CharField(max_length=100)
       slug = models.SlugField(unique=True, blank=True)# 
       image = models.ImageField(upload_to='category_images/',blank=True, null= True, validators=[FileExtensionValidator(['jpg','jpeg','png','webp'])])
       required_specs_keys = models.JSONField(default = list, blank= True)
       class Meta:
              verbose_name_plural = "Categories"
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
       slug = models.SlugField(unique=True,blank=True)
       description = models.TextField()
       price = models.DecimalField(max_digits=10, decimal_places=2)
       stock = models.PositiveIntegerField()
       is_active = models.BooleanField(default=True,db_index=True)
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)
       specifications = models.JSONField(default=dict, blank= True)
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
#Product Images (One Product -> Many Images)
class ProductImages(models.Model):
       product = models.ForeignKey(Product, related_name='images',on_delete=models.CASCADE)
       image = models.ImageField(upload_to='product_images/',validators=[FileExtensionValidator(['jpg','jpeg','png','webp'])])
       is_thumbnail = models.BooleanField(default=False)
       MAX_IMAGE_SIZE = (800, 800)
       JPEG_QUALITY = 70# Which image show on the list page ?
       def save(self,*args, **kwargs):
              if self.image:
                     img = Image.open(self.image) # Opening the Image using Pillow
                     img = img.convert('RGB') # Converting to RGB (Crusial for JPEG/Webp compatibilty)

                     if img.width > 800 or img.height > 800:
                            img.thumbnail(self.MAX_IMAGE_SIZE)
                     output = io.BytesIO() # Save to a Memory buffer
                     img.save(output,format='JPEG',quality = self.JPEG_QUALITY)
                     output.seek(0)
                     self.image = ContentFile(output.getvalue(), name=self.image.name)
                     super().save(*args, **kwargs)

       def __str__(self):
              return f"Image for {self.product.name}"
class ProductVariant(models.Model):
       product = models.ForeignKey(Product,related_name='variants', on_delete=models.CASCADE)
       attribute_name = models.CharField(max_length=100)
       attribute_value = models.CharField(max_length=255)
       color = models.CharField(max_length=50, blank=True, null=True)

       price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)#to set different price for different variant
       
       stock = models.PositiveIntegerField(default=0) # Each variant have different stock
       
       is_active = models.BooleanField(default=True)

       def __str__(self):
              return f"{self.product.name} - {self.attribute_name}: {self.attribute_value} ({self.color})"

class InventoryUnit(models.Model):

       STATUS_CHOICES =  (
              ('In Stock','In Stock'),# The first value in the inner tuple is what gets saved to the database (e.g. 'In Stock'). The second value is what gets displayed to humans in the Django Admin interface or dropdown menus
              ('Reserved','Reserved'),
              ('Sold','Sold'),
              ('Returned','Returned'),
       )

       product = models.ForeignKey(Product,related_name='inventory_units',on_delete=models.CASCADE)
       variant = models.ForeignKey(ProductVariant,related_name='inventory_units',on_delete=models.CASCADE,null=True,blank=True)
       serial_number = models.CharField(max_length=100,unique=True,db_index=True) # db_index = True make the serial_number index 
       status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='in Stock',db_index=True)
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



