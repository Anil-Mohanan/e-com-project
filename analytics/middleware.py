from analytics.models import AuditLog
from rest_framework_simplejwt.authentication import JWTAuthentication

import logging

logger = logging.getLogger(__name__)

class AuditLogMiddleware:

       def __init__(self,get_response):
              self.get_response = get_response

       def __call__(self,request):

              response = self.get_response(request)
              user_id = None
              auth_header = request.META.get('HTTP_AUTHORIZATION') # Grabbing the JWT Token
              
              if auth_header and auth_header.startswith('Bearer '):
                     
                     try:
                            raw_token = auth_header.split(' ')[1] # Spliting only the Token Witout Bearer
       
                            jwt_authenticator = JWTAuthentication()
                            validated_token = jwt_authenticator.get_validated_token(raw_token) 

                            user_id = validated_token['user_id']
                     except Exception as e:
                            pass

              path = request.path
              method = request.method
              status_code = response.status_code 
              ip_address = request.META.get('REMOTE_ADDR')

              AuditLog.objects.create(
                      user_id= user_id,
                      Path= path,
                      method= method,
                      status_code= status_code,
                      ip_address= ip_address
              )

              return response