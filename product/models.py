from django.db import models
from django.utils.text import slugify
from user_auth.models import User
from django.core.validators import FileExtensionValidator
from PIL import Image
import io
from django.core.files.base import ContentFile
#Category model

class Category(models.Model):
       name = models.CharField(max_length=100)
       slug = models.SlugField(unique=True, blank=True)# 
       image = models.ImageField(upload_to='category_images/',blank=True, null= True, validators=[FileExtensionValidator(['jpg','jpeg','png','webp'])])

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
       name = models.CharField(max_length=200)
       brand = models.CharField(max_length=100, blank=True, null=True)
       slug = models.SlugField(unique=True,blank=True)
       description = models.TextField()
       price = models.DecimalField(max_digits=10, decimal_places=2)
       stock = models.PositiveIntegerField()
       is_active = models.BooleanField(default=True)
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       def save(self,*args,**kwargs):
              if not self.slug:
                     self.slug = slugify(self.name)
              super().save(*args,**kwargs)
       def __str__(self):
              return self.name
#Product Images (One Product -> Many Images)
class ProductImages(models.Model):
       product = models.ForeignKey(Product, related_name='images',on_delete=models.CASCADE)
       image = models.ImageField(upload_to='product_images/',validators=[FileExtensionValidator(['jpg','jpeg','png','webp'])])
       is_thumbnail = models.BooleanField(default=False)# Which image show on the list page ?
       def save(self,*args, **kwargs):
              super().save(*args, **kwargs)
              img = Image.open(self.image.path)# Opening the Image using Pillow
              img = img.convert('RGB') # Converting to RGB (Crusial for JPEG/Webp compatibilty)

              if img.width > 800 or img.height > 800:
                     img.thumbnail((800,800))
              output = io.BytesIO() # Save to a Memory buffer
              img.save(output,format='JPEG',quality = 70)
              output.seek(0)
              self.image.save(
                     self.image.name,
                     ContentFile(output.read()),
                     save= False
              )
       def __str__(self):
              return f"Image for {self.product.name}"
class ProductVariant(models.Model):
       product = models.ForeignKey(Product,related_name='variants', on_delete=models.CASCADE)
       size = models.CharField(max_length=200, blank=True, null=True)
       color = models.CharField(max_length=50, blank=True, null=True)

       price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)#to set different price for different variant
       
       stock = models.PositiveIntegerField(default=0) # Each variant have different stock
       
       is_active = models.BooleanField(default=True)

       def __str__(self):
              return f"{self.product.name} - {self.size}/{self.color}"

class Review(models.Model):
       product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name= 'reviews')              
       user = models.ForeignKey(User, on_delete=models.CASCADE)
       rating = models.IntegerField(default=0)
       comment = models.TextField(default="",blank=True, null=True)
       created_at  = models.DateTimeField(auto_now_add=True)

       def __str__(self):
              return f"{self.user.first_name} - {self.product.name} ({self.rating} Stars)"
              




