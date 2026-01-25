from django.db import models
from django.conf import settings
from product.models import Product

# Create your models here.

class Order(models.Model):
       ORDER_STATUS = (
              ('Cart', 'Cart'),
              ('Pending', 'Pending'),
              ('Shipped', 'Shipped'),
              ('Cancelled', 'Cancelled'),
       )

       user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
       status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Cart')
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       def __str__(self):
              return f"Orders {self.id} - {self.user.email} ({self.status})"
       @property
       def total_price(self):
              return sum(item.total_price for item in self.items.all())# Calculate total automatically from items
class OrderItem(models.Model):
       order = models.ForeignKey(Order,on_delete=models.CASCADE, related_name='items')
       product = models.ForeignKey(Product,on_delete=models.CASCADE)
       quantity = models.PositiveIntegerField(default=1)
       price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, blank=True)

       
       def save(self,*args, **kwargs):
              if not self.price_at_purchase:
                     self.price_at_purchase = self.product.price
              super().save(*args,**kwargs)
       @property
       def total_price(self):
              return self.price_at_purchase * self.quantity
       
       def __str__(self):
              return f"{self.quantity} x {self.product.name}"
              
