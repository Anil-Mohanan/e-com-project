import time
import logging
import traceback
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)

class ReqeustTimeMiddleware:
       """Measure how long every single API request takes to process. If it takes longer than 1 second, it logs a WARNING!"""

       def __init__(self,get_response):
              self.get_response = get_response

       def __call__(self,request):

              start_time = time.time() # starting the Stop StopWatch

              response = self.get_response(request) # the request response is going to the whole process (url-> viwes->models->serializer-> then coming back)

              duration = time.time() - start_time # Stop the StopWatch 

              milliseconds = round(duration * 1000)

              message =  f"[{request.method}] {request.path} - took {milliseconds}"

              if milliseconds > 1000:
                     logger.warning(f"Slow API {message}")
              else:
                     logger.info(f"Fast API: {message}")

              return response

class GlobalExceptionMiddleware: # MiddleWare to check if there any Fatel error and respond with in a nice JSON format to the Frontend

       def __init__(self,get_response):
              self.get_response = get_response
       
       def __call__(self,request):

              response = self.get_response(request)

              return response
       
       def process_exception(self,request,exception):

              logger.error(f"Bug : {exception}\n{traceback.format_exc()}")

              return JsonResponse({
                     "error": "Internal Server Error",
                     "message" : "An unexpected error occurred.our engineers have been notified"
              },status = 500)

class IpBlacklistingMiddleware: # Middle Ware that does not aprove any Banned ID

       def __init__(self,get_response):
              self.get_response = get_response
       
       def __call__(self,request):
              
              user_ip = request.META.get('REMOTE_ADDR')

              banned_ips = getattr(settings, 'BANNED_IPS',[])

              if user_ip in banned_ips:

                     logger.warning(f"BLOCKED IP:{user_ip} tried to access {request.path}")

                     return JsonResponse({"error": "Your IP address has been banned."},status = 403)

              response = self.get_response(request)

              return response