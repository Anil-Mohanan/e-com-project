from django.core.cache import cache
from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication

import logging

logger = logging.getLogger(__name__)

class UpdateLastActivityMiddleware:

       def __init__(self,get_response):
              
              self.get_response = get_response
       
       def __call__(self,request):
              
              auth_header = request.META.get('HTTP_AUTHORIZATION') # Grabbing the JWT Token

              if auth_header and auth_header.startswith('Bearer '):

                     raw_token = auth_header.split(' ')[1] # Spliting only the Token Witout Bearer
                     
                     try:
                            jwt_authenticator = JWTAuthentication()
                            validated_token = jwt_authenticator.get_validated_token(raw_token)
                            
                            user_id = validated_token['user_id'] # Grabbing User_id from token
                            cache_key = f"last_active_user_{user_id}"
                            cache.set(cache_key,timezone.now(),300)
                     except Exception as e:
                            pass

              return self.get_response(request)
                     
