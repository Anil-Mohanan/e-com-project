from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc,context):

       response = exception_handler(exc, context)# This like ask the DRF what is the error . if DRF recoginze it the response will have data in it about the error 

       if response is not None:
              
              custom_data = {
                     
                     'success': False,
                     'error_type': exc.__class__.__name__, # a varible holding actual exception 
                     'details': response.data
              }
              logger.error(f"Handled Exception: {exc}")

              response.data = custom_data
       else:
              logger.exception("Unhadled Server Error ouccured")

              return Response({'success':False,'error_type':exc.__class__.__name__,'details':str(exc)})


       return response