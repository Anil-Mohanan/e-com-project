from django.db import models
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
       order_id = models.UUIDField(db_index = True,unique= True)
       # Store the ID from the GateWay 
       transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

       payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICE)
       amount = models.DecimalField(max_digits=10, decimal_places=2)
       status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
       
       created_at = models.DateTimeField(auto_now_add=True)

       def __str__(self):
              return f"{self.payment_method} - {self.amount} - {self.status}"
       
class PaymentEventOutbox(models.Model):

       event_type = models.CharField(max_length = 255)
       payload = models.JSONField(default = dict)
       created_at = models.DateTimeField(auto_now_add=True)
       processed = models.BooleanField(default= False, db_index=True)
       processed_at = models.DateTimeField(null = True,blank= True)
       error_message = models.TextField(null = True, blank=True)
       retry_count = models.PositiveIntegerField(default=0)
