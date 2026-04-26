from .domain import ShippingStrategy, StandardShippingStrategy, IndianGSTStrategy
from .domain import calculate_order_total
from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
from django.db.models import Sum

# Create your models here.
         
class ShippingAddress(models.Model):
       user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
       full_name = models.CharField(max_length=100)# who receives the package?
       address_line_1 = models.CharField(max_length=255)
       address_line_2 = models.CharField(max_length=255, blank=True, null= True)
       city = models.CharField(max_length=100)
       state = models.CharField(max_length=100)
       postal_code = models.CharField(max_length=20)
       country = models.CharField(max_length=100,default='India')
       phone_number = models.CharField(max_length=15)
       
       #Is this the primary address?
       is_default = models.BooleanField(default=False)

       def __str__(self):
              return f"{self.full_name} - {self.city}"

class OrderQuerySet(models.QuerySet):
       
       def valid_sales(self):
              return self.exclude(status__in = ["Cart", "Cancelled","Pending"])

       def for_user(self,user):
              return self.filter(user = user)

       def current_cart(self,user):
              return self.filter(user = user, status = "Cart")

       def get_or_create_cart(self,user):
              cart, created = self.get_or_create(user = user, status = 'Cart')
              return cart , created

class Order(models.Model):
       ORDER_STATUS = (
              ('Cart', 'Cart'),
              ('Pending', 'Pending'),
              ('OrderConfirmed','OrderConfirmed'),
              ('Shipped', 'Shipped'),
              ('Delivered', 'Delivered'),
              ('Cancelled', 'Cancelled'),
       )
       objects = OrderQuerySet.as_manager()
       user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,null = True , related_name='orders')
       shipping_address = models.ForeignKey(ShippingAddress,on_delete=models.SET_NULL, null=True, blank=True)#deleting an address from your profile, we don't want to delete all the historical orders sent to that address. We just keep the order but say "Address was deleted".
       status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Cart',db_index=True)
       created_at = models.DateTimeField(auto_now_add=True,db_index=True)
       updated_at = models.DateTimeField(auto_now=True)
       order_id = models.UUIDField(default=uuid.uuid4,editable=False, unique=True)
       total_price = models.DecimalField(max_digits=10,decimal_places=2, default=0.00)
       is_paid = models.BooleanField(default=False)
       paid_at = models.DateTimeField(auto_now_add=False , null = True, blank=True)

       def __str__(self):
              return f"Orders {self.order_id} - {self.user.email} ({self.status})"

       @property
       def subtotal(self):#price of items only
              return sum(item.total_price for item in self.items.all())
       @property
       def tax_amount(self):#tax calculation
              strategy = IndianGSTStrategy()
              return strategy.calculate_tax(self.subtotal)
       @property
       def shipping_fee(self):#shipping fee over 1500
             strategy = StandardShippingStrategy()
             return strategy.calculate_fee(self.subtotal)
       
       def calculate_total(self):
              return calculate_order_total(self.subtotal,StandardShippingStrategy(),IndianGSTStrategy())

       def save(self,*args,**kwargs):
              # calling the parent to carete the row in the DB (We need an ID!)

              super().save(*args,**kwargs)
              #
              new_total = self.calculate_total()
              
              if self.total_price != new_total:
                     self.total_price = new_total
                     super().save(update_fields=['total_price'])

class OrderItemQuerySet(models.QuerySet):
       
       def top_selling(self,limit=5):
              return self.values('product_name').annotate(total_sold = Sum('quantity')).order_by('-total_sold')[:limit]
       
class OrderItem(models.Model):
    objects = OrderItemQuerySet.as_manager()   
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_id = models.IntegerField(db_index=True)
    variant_id = models.IntegerField(db_index=True,null=True,blank=True)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    
    # We keep this blank allowed, because while in 'Cart', it might be empty
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def total_price(self):
        # CRITICAL LOGIC FIX:
        # If the price is locked (Order is placed), use that.
        # If the price is NOT locked (Still in Cart), use the LIVE product price.
       return (self.price_at_purchase or 0) * self.quantity
@receiver(post_save, sender=  OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total(sender,instance, **kwargs):
       """
    When an Item is added/modified/deleted, tell the Parent Order to re-save.
    Re-saving triggers the 'save()' method above, which updates the price.
    """
       instance.order.save()
    

class OrderEventOutbox(models.Model): # Event Box that store the Even in SQL in case the redis failed the event stits here safily
       event_type = models.CharField(max_length = 255)
       payload = models.JSONField(default=dict)
       created_at = models.DateTimeField(auto_now_add=True)
       processed = models.BooleanField(default=False,db_index= True)
       processed_at = models.DateTimeField(null = True,blank=True)
       error_message = models.TextField(null=True,blank=True)
       retry_count = models.PositiveIntegerField(default=0)
       


