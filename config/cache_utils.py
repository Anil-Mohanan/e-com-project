from django.core.cache import cache
from rest_framework.response import Response
from functools import wraps
from config.utils import error_response
import hashlib
import logging

logger = logging.getLogger(__name__)

def cache_response(key_prefix,timeout = 900, error_message = "Service temporarily Unavailable", user_specific=False, allowed_params = None):
       """A custom decorateor that automaticaly handles caching, reading, writing , and error loggingfor django REST_FRAMEWORK views"""

       def decorateor(view_func): # view_func is literally the list()or retrieve() method that you wrote in product/views.py. Python grabs your entire function and hands it into here.
              @wraps(view_func)
              def _wrapped_view_func(self,request,*args,**kwargs):
                     query_dict = {}
                     if allowed_params is None:
                            query_dict = dict(request.query_params.items())
                     else:
                            for key in request.query_params:
                                   if key in allowed_params:
                                          query_dict[key] = request.query_params.get(key)

                     identifier = "_".join(str(v)for v in kwargs.values())

                     sorted_items = sorted(query_dict.items())
                     param_string = "&".join([f"{k}={v}" for k, v in sorted_items])
                     hashed_params = hashlib.md5(param_string.encode()).hexdigest() if param_string else ""

                     cache_key = key_prefix
                     version = cache.get(f"{key_prefix}_version")
                     if version:
                            cache_key += f"_v{version}"
                            
                     if user_specific and request.user.is_authenticated:
                            cache_key += f"_user_{request.user.id}"
                     if identifier:
                            cache_key += f"_{identifier}"
                     if hashed_params:
                            cache_key += f"_{hashed_params}"

                     try: # Check the is there is cache
                            stored_data = cache.get(cache_key)
                            if stored_data:
                                   return Response(stored_data)
                     except Exception as e:
                            logger.error(f"Cache Read Error on {key_prefix} : {e}")
                            
                     try: # Fetching From DB
                            response = view_func(self,request,*args,**kwargs)
                     
                     except Exception as e:
                            return error_response(message=error_message, status_code=500, log_message=f"DB Error on {key_prefix} : {e}")

                     try:
                            cache.set(cache_key, response.data, timeout)
                     except Exception as e:
                            logger.error(f"Cache Write Error on {key_prefix} : {e}")

                     return response
              return _wrapped_view_func
       return decorateor