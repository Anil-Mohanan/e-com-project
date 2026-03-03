from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, UserSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
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
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from .models import UserDeviceSession

import logging

User = get_user_model()
logger = logging.getLogger(__name__)
class RegisterView(generics.CreateAPIView):# using generics for safety reasons , generics only do one specfic method one at a time
       queryset = User.objects.all()
       serializer_class = UserRegistrationSerializer
       permission_classes = [AllowAny]# Anyone must be able to register!
       
       def perform_create(self, serializer):
              user = serializer.save()
              
              uid = urlsafe_base64_encode(force_bytes(user.pk))  # :urlsafe_base64_encode takes the user's Primary Key (like 15) and turns it into a string (like MTU)
              token = default_token_generator.make_token(user) #default_token_generator.make_token creates a one-time-use string based on the user's password and the current time. It's the "key" that proves the link is real
              
              link = reverse('verify_email', kwargs={'uidb64': uid, 'token' : token})       

              verification_url = f"http://127.0.0.1:8000{link}"

              send_mail('Verify your email',f"Click here :{verification_url}",'from@example.com',[user.email])
              
class LogoutView(APIView):
       permission_classes = [IsAuthenticated]
       def post(self,request):
              try :
                     refresh_token = request.data["refresh"]

                     token = RefreshToken(refresh_token)

                     token.blacklist()
                     
                     return Response({"message" : "Successfully logged Out"}, status=status.HTTP_205_RESET_CONTENT)
              except Exception as e:
                     return error_response(message="Unable to Log Out. Please Try again",status_code=400,log_message=f"Token Error in LogOutView : {e}")
              
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
                     return error_response(message="Unable to delete Account At this Moment", status_code=401, log_message=f"Error in DeleteAccountView : {e}")
              
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


class CustomTokenObtainPairView(TokenObtainPairView):
       """custom loig Ve that use custom serialzer to check for email verification and update last login time """

       serializer_class = CustomTokenObtainPairSerializer

class ActiveSessionView(APIView):
       permission_classes = [IsAuthenticated]

       def get(self,request):
              try:
                     tokens = OutstandingToken.objects.filter(user = request.user)   # Django will return a list contianing every single refresh token
                      
                     active_sessions = []
                     for token in tokens:
                            if not hasattr(token,'blacklistedtoken'):
                                   ip_add = "Unknown"
                                   device = "Unknown"
                                   try:
                                          device_session = UserDeviceSession.objects.get(jti = token.jti)
                                          ip_add = device_session.ip_address
                                          device = device_session.device_name

                                   except UserDeviceSession.DoesNotExist:
                                          pass

                                   active_sessions.append({
                                          "jti": token.jti,
                                          "created_at": token.created_at,
                                          "expires_at": token.expires_at,
                                          "ip_address" : ip_add,
                                          "device_name": device,
                                   })
                     return Response(active_sessions)
              except Exception as e:
                     return error_response(message="No ActiveSession Found",status_code=404,log_message=f"Error in ActiveSessionView : {e}")


class RevokedDevicesView(APIView):

       permission_classes = [IsAuthenticated]

       def post(self,request):
              
              token_jti = request.data.get('jti')

              if not token_jti:
                            return Response({"message": "JTI is Required"},status=status.HTTP_400_BAD_REQUEST)
              try:
                     token = OutstandingToken.objects.get(jti = token_jti, user = request.user) # find the OutstandingToken token using JTI

                     BlacklistedToken.objects.get_or_create(token = token) # Blacklisting only the specfic device session

                     return Response({"message": "Logout Sucess from the device"})
              except OutstandingToken.DoesNotExist:
                     return error_response(message='Session not found or already logged out', status_code=404, log_message="Error in RevokedDevicesView")

                     