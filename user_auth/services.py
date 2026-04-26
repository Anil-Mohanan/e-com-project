from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from . import repositories as default_repo
from .strategies import RegistrationStrategy, EmailPasswordRegistrationStrategy
import logging

logger = logging.getLogger(__name__)

def verify_email_process(uidb64,token,repo = default_repo):
       try:
              uid = force_str(urlsafe_base64_decode(uidb64))
              user = repo.get_user_by_id(uid)
       except (TypeError, ValueError, OverflowError):
              return False
       
       if user is not None and default_token_generator.check_token(user,token):
              repo.verify_user_email(user)
              return True
       
       return False

def get_user_active_sessions(user, repo=default_repo):
       return repo.get_active_sessions(user)

def revoke_device_access(user, token_jti, repo=default_repo):
       if not token_jti:
              raise ValueError("JTI is Required")

       success = repo.revoke_device_session(user,token_jti)
       if not success:
              raise ValueError("Session not Found or already logged Out")

def process_user_registration(user,version = 'v1',strategy: RegistrationStrategy = EmailPasswordRegistrationStrategy()):

       """
       DEPENDENCY INVERSION: The service doesn't care HOW the user registered.
       It just executes the provided strategy.
       """
       strategy.process_post_registration(user, version)
