from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

# Create your models here.
class CustomUserManager(BaseUserManager):
       def create_user(self,email, password = None, **extra_fields):
              if not email:
                     raise ValueError('The Email field must be set')
              email = self.normalize_email(email)#Normalization converting anything in the email to lowecase
              user = self.model(email = email, **extra_fields)#  self.model refers to your User class. This creating a python objects in the memeory it puts the clean email and the extra feild into the user model Note: It hasn't touched the database yet.
              user.set_password(password)
              #set_password() takes your plain text password and turns it into a hash like pbkdf2_sha256$260000$..... It is irreversible.
              user.save(using=self._db)# Saving the the user to the PostgreSQL DB
              
              return user
       def create_superuser(self,email,password = None, **extra_fields):
              extra_fields.setdefault('is_staff',True)
              extra_fields.setdefault('is_superuser',True)
              extra_fields.setdefault('is_active',True)

              if extra_fields.get('is_staff') is not True:
                     raise ValueError('Superuser must have is_staff=True.')
              if extra_fields.get('is_superuser') is not True:
                     raise ValueError('Superuser must have is_superuser=True.')
              return self.create_user(email,password,**extra_fields)
              
#The model Body
class User(AbstractUser):
       username = models.CharField(max_length=150, unique=True , null=True, blank=True)
       email = models.EmailField(unique=True)

       is_customer = models.BooleanField(default=True)
       is_seller = models.BooleanField(default=False)
       
       objects = CustomUserManager()

       USERNAME_FIELD = 'email'
       REQUIRED_FIELDS = []

       def __str__(self):
              return self.email
       