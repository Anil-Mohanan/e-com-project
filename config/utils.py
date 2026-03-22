from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


# config/utils.py
def error_response(message="An unexpected error occurred.", status_code=500, log_message=None):
    if log_message:
        logger.error(log_message)
    return Response(
        {"success": False, "error_type": "ApplicationError", "details": {"non_field_errors": [message]}},
        status=status_code
    )

def success_response(data = None,message = 'Success', status_code = 200):
    """Standridzie API success response so that frontend has predictable JSON Shape"""
    response_data = {
        "success" : True,
        "message" : message,
    }
    if data is not None:
        response_data["data"] = data
        
    return Response(response_data,status=status_code)
