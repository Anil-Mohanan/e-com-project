from rest_framework import response
import logging

logger = logging.getLogger(__name__)

def error_response(message = "An unexpected Error occured.",status_code = 500,log_message = None):
       """Standardize API error response and logs the error simultaneously"""

       if log_message: #1 log the detailde error for the devloper
              logger.error(log_message)
       
       return response(
              {"error": message},
              status = status_code
       )
