from abc import ABC, abstractmethod
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.db import transaction
from django.conf import settings
from user_auth.tasks import task_send_verification_email

class RegistrationStrategy(ABC):
       @abstractmethod
       def process_post_registration(self,user,version: str = "v1"):
              pass
# user_auth/domain/strategies.py
from django.conf import settings

class EmailPasswordRegistrationStrategy(RegistrationStrategy):
    def process_post_registration(self, user, version: str = 'v1'):
       uid = urlsafe_base64_encode(force_bytes(user.pk))
       token = default_token_generator.make_token(user)
       
       # Use settings, NOT hardcoded strings
       verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}"
       # THE SENIOR MOVE: Save to Outbox. 
       # If Redis is down, the user still gets registered.
       from user_auth.models import AuthEventOutbox
       AuthEventOutbox.objects.create(
           event_type='auth.registration_email',
           payload={
               'email': user.email,
               'url': verification_url
           }
       )

class GoogleOAuthRegistrationStrategy(RegistrationStrategy):
       def process_post_registration(self, user, version: str = 'v1'):
              # Google already verified their email!
              # So we just mark them as verified immediately.
              user.is_active = True
              # If you have an `is_verified` field, you would set it here too
              user.save(update_fields=['is_active'])
              print(f"Google OAuth User {user.email} verified automatically.")