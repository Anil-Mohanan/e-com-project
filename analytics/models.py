from django.db import models
from django.conf import settings

# Create your models here.
class AuditLog(models.Model):
       
       user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)#We use models.SET_NULL for the User so that if you ever delete a user from your database, you don't accidentally delete the audit history of what they did       
       
       method = models.CharField(max_length=10)

       Path = models.CharField(max_length=255)

       status_code = models.IntegerField()

       ip_address = models.GenericIPAddressField(null=True, blank=True)

       created_at = models.DateTimeField(auto_now_add=True, db_index = True)

       def __str__(self):
              return f"[{self.method}] {self.Path} - {self.status_code}"
       
       class Meta:
              indexes = [models.Index(fields = ['user','-created_at'])]

class AdminActionLog(models.Model):
       """
       Semantic admin action log - tracks what changed , not just that a request happend.
       This is the compliance layer . AuditLog tracks HTTP traffic.
       AdminActionLog tracks business decisions.

       """

       ACTION_CHOICES = (
              ('order.status_changed','Order Status Changed'),
              ('product.price_changed', 'Product Price Changed'),
              ('product.stock_adjusted', 'Product Stock Adjusted'),
       )
       actor_id = models.IntegerField(null = True, blank=True)# The admin user who performed the action. Integerfield (not Fk ) so that deleting a user dosn't delete their action history

       actor_email = models.CharField(max_length=255,blank=True, default = '')
       #store the email at time of action - even if the account is later deleted,

       action = models.CharField(max_length = 100,choices = ACTION_CHOICES, db_index = True)
       # db_index because admins will filter logs by action type constantly

       target_id = models.CharField(max_length=100)
       #track which order or product was changed

       old_value = models.JSONField(null = True, blank = True)
       # What it was BEFORE the change - the before snapshot

       new_value = models.JSONField(null = True, blank = True)
       # what it became After the change - the after snapshot

       timestamp = models.DateTimeField(auto_now_add = True, db_index = True)

       class Meta:
              ordering = ['-timestamp'] # most recent actions first - the default view in the admin list

       def __str__(self):
              return f"{self.actor_email} -> {self.action} on {self.target_id}"