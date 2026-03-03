from django.db import models
from django.conf import settings
# Create your models here.
class AuditLog(models.Model):
       
       user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)#We use models.SET_NULL for the User so that if you ever delete a user from your database, you don't accidentally delete the audit history of what they did       
       
       method = models.CharField(max_length=10)

       Path = models.CharField(max_length=255)

       status_code = models.IntegerField()

       ip_address = models.GenericIPAddressField(null=True, blank=True)

       created_at = models.DateTimeField(auto_now_add=True)

       def __str__(self):
              return f"[{self.method}] {self.Path} - {self.status_code}"
       