from config.utils import error_response

def error_404(request,exception):
       """Global Hanlers for 404 Not Found errros."""

       return error_response(
              message="The requested resource was not found on this server",
              status_code=404,
              log_message=f"Global 404 triggered at: {request.path}"
       )
def error_500(request):
       """Global handler for 500 Server Errors."""

       return error_response(
              message="An internal server error occurred. Our team has been notified.",
              log_message="Global 500 Triggered."
       )