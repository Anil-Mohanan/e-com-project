from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created , post_password_reset#The library django-rest-passwordreset triggers this event specifically when someone hits the /password_reset/ endpoint.
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

from django.conf import settings # Add this at top

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
       print(f"DEBUG: PASSWORD RESET SIGNAL TRIGGERED FOR {reset_password_token.user.email}")
       from user_auth.models import AuthEventOutbox
       
       # We point the user to the FRONTEND Reset page
       reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_password_token.key}" 
       
       AuthEventOutbox.objects.create(
           event_type='auth.password_reset',
           payload={
               'email': reset_password_token.user.email,
               'url': reset_url
           }
       )

              
              
@receiver(post_password_reset)
def increase_token_version(sender,user,*args,**kwargs):
       user.jwt_version += 1
       user.save()