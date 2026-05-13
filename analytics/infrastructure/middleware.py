from analytics.models import AuditLog
from rest_framework_simplejwt.authentication import JWTAuthentication
from analytics.tasks import log_api_request_task

import logging

logger = logging.getLogger(__name__)

class AuditLogMiddleware:

       def __init__(self,get_response):
              self.get_response = get_response

       def __call__(self,request):

              if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
                     # It stops the unnecessary database writing by using a concept called an "Early Return" (also known as a "Guard Clause").
                     return self.get_response(request)

              if request.method == 'GET' and request.path.startswith('/api/products/'):

                     return self.get_response(request)

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

              try:
                     log_api_request_task.delay(user_id,path,method,status_code,ip_address)
              except Exception as e:

                     logger.error(f"Celery task failed: {e}")

              return response