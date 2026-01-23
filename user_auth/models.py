from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
       username = None # Remove username field
       email = models.EmailField(unique=True)

       is_customer = models.BooleanField(default=True)
       is_seller = models.BooleanField(default=False)

       USERNAME_FIELD = 'email'
       REQUIRED_FIELDS = []

       def __str__(self):
              return self.email
       