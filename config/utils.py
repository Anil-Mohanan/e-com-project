from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


def error_response(
        message="An unexpected error occurred.",
        status_code=500,
        log_message=None
):
    """Standardize API error response and log the error simultaneously"""

    if log_message:
        logger.error(log_message)

    return Response(
        {"error": message},
        status=status_code
    )
