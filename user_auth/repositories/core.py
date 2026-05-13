from django.contrib.auth import get_user_model
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from user_auth.models import UserDeviceSession
from user_auth.domain import SessionDTO

User = get_user_model()

#---------- Email Verfication ----------

def get_user_by_id(uid):
       try:
              return User.objects.get(pk = uid)
       except User.DoesNotExist:
              return None

def verify_user_email(user):

       user.is_email_verified = True
       user.save()

# ------- Session Management -------

def get_active_sessions(user):
       tokens = OutstandingToken.objects.filter(user = user)
       active_session = []

       for token in tokens:
              # check if token is BlacklistedToken
              if not hasattr(token, 'blacklistedtoken'):
                     ip_add = "Unknown"
                     device = "Unknown"

                     try:
                            device_session = UserDeviceSession.objects.get(jti = token.jti)
                            ip_add = device_session.ip_address
                            device = device_session.device_name
                     except UserDeviceSession.DoesNotExist:
                            pass

                     active_session.append(SessionDTO(
                            jti = token.jti,
                            created_at = token.created_at,
                            expires_at = token.expires_at,
                            ip_address = ip_add,
                            device_name = device
                     ))

       return active_session

def revoke_device_session(user,token_jti):
       try:
              token = OutstandingToken.objects.get(jti = token_jti, user = user)
              BlacklistedToken.objects.get_or_create(token = token)

              return True
       except OutstandingToken.DoesNotExist:
              return False