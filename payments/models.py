from django.db import models
from orders.models import Order
from django.conf import settings

# Create your models here.
class Payment(models.Model):
       PAYMENT_METHOD_CHOICE = (
              ('Stripe','Stripe'),
       )
       
       STATUS_CHOICES = (
              ('Pending', 'Pending'),
              ('Success', 'Success'),
              ('Failed', 'Failed'),
       )
       # Link to the Order (One Payment per Order)
       order = models.OneToOneField(Order,on_delete=models.CASCADE, related_name='payment')
       # Store the ID from the GateWay 
       transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

       payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICE)
       amount = models.DecimalField(max_digits=10, decimal_places=2)
       status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
       
       created_at = models.DateTimeField(auto_now_add=True)

       def __str__(self):
              return f"{self.payment_method} - {self.amount} - {self.status}"

              

