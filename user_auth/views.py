from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes , force_str
from django.core.mail import send_mail
from django.urls import reverse
from config.utils import error_response
import logging

User = get_user_model()
logger = logging.getLogger(__name__)
class RegisterView(generics.CreateAPIView):# using generics for safety reasons , generics only do one specfic method one at a time
       queryset = User.objects.all()
       serializer_class = UserRegistrationSerializer
       permission_classes = [AllowAny]# Anyone must be able to register!

class LogoutView(APIView):
       permission_classes = [IsAuthenticated]
       def post(self,request):
              try :
                     refresh_token = request.data["refresh"]

                     token = RefreshToken(refresh_token)

                     token.blacklist()
                     
                     return Response({"message" : "Successfully logged Out"}, status=status.HTTP_205_RESET_CONTENT)
              except Exception as e:
                     return error_response(message="Unable to Log Out. Please Try again",status_code=500,log_message=f"Token Error in LogOutView : {e}")
              
class UserProfileView(generics.RetrieveUpdateAPIView):
       queryset = User.objects.all()
       serializer_class = UserSerializer
       permission_classes = [IsAuthenticated]

       def get_object(self):
              return self.request.user
       def update(self, request, *args, **kwargs):
              try:
                     return super().update(request,*args,**kwargs)
              except Exception as e:
                     return error_response(message="Unable to update profile at this time", status_code=500, log_message=f"Error  in UserProfileView update method : {e}")
              
class DeleteAccountView(APIView):
       permission_classes = [IsAuthenticated]

       def delete(self, request):
              try:
                     user = request.user
                     user.delete()
                     return Response({"message": "Account deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
              except Exception as e:
                     return error_response(message="Unable to delete Account At this Moment", status_code=500, log_message=f"Error in DeleteAccountView : {e}")
class VerifyEmailView(APIView):
       def get(self,request,uidb64,token):
              try:
                     uid = force_str(urlsafe_base64_decode(uidb64))
                     user = User.objects.get(pk=uid)
              except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                     user = None
              try:
                     if user is not None and default_token_generator. check_token(user,token):
                            user.is_email_verified = True
                            user.save()
                            return Response({"message": "Email verified Successfully!"}, status=status.HTTP_200_OK)
                     else:
                            return Response({"error": "Invalid Link"}, status=status.HTTP_400_BAD_REQUEST)
              except Exception as e:
                     return error_response(message="Unable to Verify Email at this moment", status_code=500, log_message=f"Error in VerifyEmailView : {e}")