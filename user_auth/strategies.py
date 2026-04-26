from abc import ABC, abstractmethod
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.db import transaction
from .tasks import task_send_verification_email

class RegistrationStrategy(ABC):
       @abstractmethod
       def process_post_registration(self,user,version: str = "v1"):
              pass
class EmailPasswordRegistrationStrategy(RegistrationStrategy):
       def process_post_registration(self, user, version: str = 'v1'):
              
              uid = urlsafe_base64_encode(force_bytes(user.pk))  # :urlsafe_base64_encode takes the user's Primary Key (like 15) and turns it into a string (like MTU)
              token = default_token_generator.make_token(user) #default_token_generator.make_token creates a one-time-use string based on the user's password and the current time. It's the "key" that proves the link is real

              link = reverse('verify_email',kwargs={'uidb64':uid,'token': token, 'version': version})

              verification_url =  f"http://127.0.0.1:8000{link}"
              transaction.on_commit(lambda:task_send_verification_email.delay(user.email,verification_url))

class GoogleOAuthRegistrationStrategy(RegistrationStrategy):
       def process_post_registration(self, user, version: str = 'v1'):
              # Google already verified their email!
              # So we just mark them as verified immediately.
              user.is_active = True
              # If you have an `is_verified` field, you would set it here too
              user.save(update_fields=['is_active'])
              print(f"Google OAuth User {user.email} verified automatically.")