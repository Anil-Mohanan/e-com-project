from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created , post_password_reset#The library django-rest-passwordreset triggers this event specifically when someone hits the /password_reset/ endpoint.
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

@receiver(reset_password_token_created)#Whenever the reset_password_token_created event happens anywhere in the app, STOP everything and run the function below immediately.
def reset_password_token_created(sender,instance, reset_password_token, *args, **kwargs):
       token = reset_password_token.key
       print(f"\n\n----- PASSWORD RESET TOKEN -----\n{token}\n--------------------------------\n")

User = get_user_model() 
              
              
@receiver(post_password_reset)
def increase_toekn_version(sender,user,*args,**kwargs):
       user.jwt_version += 1
       user.save()