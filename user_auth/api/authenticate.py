from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
       # 1. Look for the token in the cookies instead of the header
       raw_token = request.COOKIES.get('access_token') or None
       if raw_token is None:
           return None
       # 2. If we find it, validate it using the standard SimpleJWT logic
       validated_token = self.get_validated_token(raw_token)
       
       return self.get_user(validated_token), validated_token
