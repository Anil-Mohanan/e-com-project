from django.db import models
from django.utils.text import slugify

#Category model

class Category(models.Model):
       name = models.CharField(max_length=100)
       slug = models.SlugField(unique=True, blank=True)# 
       image = models.ImageField(upload_to='category_images/',blank=True, null= True)

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
       image = models.ImageField(upload_to='product_images/')
       is_thumbnail = models.BooleanField(default=False)# Which image show on the list page ?
       
       def __str__(self):
              return f"Image for {self.product.name}"
       