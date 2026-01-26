from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created #The library django-rest-passwordreset triggers this event specifically when someone hits the /password_reset/ endpoint.

@receiver(reset_password_token_created)#Whenever the reset_password_token_created event happens anywhere in the app, STOP everything and run the function below immediately.
def reset_password_token_created(sender,instance, reset_password_token, *args, **kwargs):
       token = reset_password_token.key
       print(f"\n\n----- PASSWORD RESET TOKEN -----\n{token}\n--------------------------------\n")
       