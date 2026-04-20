from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError 

# Create your models here.
class UserQuerySet(models.QuerySet):
       def seller(self):
              return self.filter(is_seller = True)

       def customer(self):
              return self.filter(is_customer = True)

class CustomUserManager(BaseUserManager.from_queryset(UserQuerySet)):
       def create_user(self,email,is_staff = False, is_superuser = False, password = None,is_email_verified=False, **extra_fields):
              if not email:
                     raise ValueError('The Email field must be set')
              
              email = email.strip()
              
              if len(email) > 255:
                     raise ValueError('Eamil is too long')
              
              try:
                     validate_email(email)

              except ValidationError:
                     raise ValueError('The Email is invalid')
              
              if not password or not password.strip():# strip()used to remove whtie space
                     raise ValueError('The Password field must be set')

              if len(password) > 128:
                     raise ValueError("Password is too long")
              
              email = self.normalize_email(email).lower()#Normalization converting anything in the email to lowecase
              
              
              extra_fields.pop('is_email_verified',None)# Striping out sensitive fields from extra_fields if they exist
              extra_fields.pop('is_staff',None)
              extra_fields.pop('is_superuser',None)
              
              user = self.model(email = email, **extra_fields)#  self.model refers to your User class. This creating a python objects in the memeory it puts the clean email and the extra feild into the user model Note: It hasn't touched the database yet.
              
              validate_password(password , user=user)
              
              
              user.is_email_verified = is_email_verified #Explicitly set the security state
              user.is_staff = is_staff
              user.is_superuser = is_superuser
              user.set_password(password)
              #set_password() takes your plain text password and turns it into a hash like pbkdf2_sha256$260000$..... It is irreversible.
              user.save(using=self._db)# Saving the the user to the PostgreSQL DB
              
              return user
       def create_superuser(self,email,password = None, **extra_fields):
              # Pre-fills the dictionary with the mandatory flags required for administrative access.
              extra_fields.setdefault('is_staff',True)
              extra_fields.setdefault('is_superuser',True)
              extra_fields.setdefault('is_active',True)

              #Extraction: Pulls the values out of the dictionary into local variables so we can pass them as 'Trusted' arguments.
              is_staff = extra_fields.pop('is_staff',True)
              is_superuser = extra_fields.pop('is_superuser',True)
              is_email_verified = extra_fields.pop('is_email_verified', True)

              if is_staff is not True:
                     raise ValueError('Superuser must have is_staff=True.')
              if is_superuser is not True:
                     raise ValueError('Superuser must have is_superuser=True.')
              return self.create_user(
                     email=email,
                     password=password,
                     is_staff=is_staff,
                     is_superuser=is_superuser,
                     is_email_verified=is_email_verified,
                     **extra_fields 
              )
              
#The model Body
class User(AbstractUser):
       username = models.CharField(max_length=150, unique=True , null=True, blank=True)
       email = models.EmailField(unique=True)
       is_email_verified = models.BooleanField(default=False)
       is_customer = models.BooleanField(default=True)
       is_seller = models.BooleanField(default=False)
       jwt_version = models.IntegerField(default=1)


       objects = CustomUserManager()

       USERNAME_FIELD = 'email'
       REQUIRED_FIELDS = []

       def __str__(self):
              return self.email
       
class UserDeviceSessionQuerySet(models.QuerySet):
       def for_user(self,user):
              return self.filter(user = user) # filter the user instantly

       def by_ip(self,ip_address):
              return self.filter(ip_address = ip_address)

class UserDeviceSession(models.Model):
       user = models.ForeignKey(User,on_delete=models.CASCADE)
       jti =  models.CharField(max_length=255,unique=True)
       ip_address =  models.GenericIPAddressField(null= True, blank=True)
       device_name = models.CharField(max_length=255, null=True, blank=True)
       created_at = models.DateTimeField(auto_now_add=True)

       objects = UserDeviceSessionQuerySet.as_manager()

       def __str__(self):
              return f"{self.user.email} - {self.device_name}"
