from rest_framework.decorators import permission_classes
from django.urls import path
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer, UserSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from config.utils import error_response, success_response
from user_auth.services import verify_email_process , get_user_active_sessions, revoke_device_access,process_user_registration
from django.conf import settings
import dataclasses

import logging

User = get_user_model()
logger = logging.getLogger(__name__)
class RegisterView(generics.CreateAPIView):# using generics for safety reasons , generics only do one specfic method one at a time
       queryset = User.objects.all()
       serializer_class = UserRegistrationSerializer
       permission_classes = [AllowAny]# Anyone must be able to register!
       
       def perform_create(self, serializer):
              user = serializer.save()
              
              version = self.kwargs.get('version','v1')
              
              process_user_registration(user,version)
              
              
class LogoutView(APIView):
       permission_classes = [AllowAny]
       def post(self, request, *args, **kwargs):
              try :
                     refresh_token = request.COOKIES.get('refresh_token') or request.data.get("refresh")

                     token = RefreshToken(refresh_token)

                     token.blacklist()
                     
                     response =  success_response(message = "Successfully logged Out", status_code = 205)

                     response.delete_cookie('access_token',path='/',samesite="Lax")
                     response.delete_cookie('refresh_token',path='/',samesite="Lax")

                     return response
                     
              except Exception as e:
                     response = error_response(message="Unable to Log Out. Please Try again",status_code=400,log_message=f"Token Error in LogOutView : {e}")

                     response.delete_cookie('access_token',path='/',samesite="Lax")
                     response.delete_cookie('refresh_token',path = '/', samesite="Lax")

                     return response
              
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

       def delete(self, request, *args, **kwargs):
              try:
                     user = request.user
                     user.delete()
                     return success_response(message = "Account deleted successfully", status_code = 204)
              except Exception as e:
                     return error_response(message="Unable to delete Account At this Moment", status_code=401, log_message=f"Error in DeleteAccountView : {e}")
              
class VerifyEmailView(APIView):

       def get(self,request,uidb64,token,*args,**kwargs):
              try:
                     is_verified = verify_email_process(uidb64, token)
                     
                     if is_verified:
                            return success_response(message="Email verified Successfully!", status_code=200)
                     else:
                            return error_response(message="Invalid Link",status_code=400)

              except Exception as e:
                     return error_response(message="Unable to Verify Email at this moment", status_code=500, log_message=f"Error in VerifyEmailView : {e}")


class CustomTokenObtainPairView(TokenObtainPairView):
       """custom loig Ve that use custom serialzer to check for email verification and update last login time """
       serializer_class = CustomTokenObtainPairSerializer
       def post(self, request, *args, **kwargs):
              refresh_token = request.COOKIES.get('refresh_token')
              if refresh_token:
            # Inject the cookie value into the request data for the parent class
                     request.data['refresh'] = refresh_token
        
              response = super().post(request, *args, **kwargs)
        
              if response.status_code == 200:
                     access_token = response.data.get('access')
                            # Set the new access token in the cookie
                     response.set_cookie(
                     key='access_token',
                     value=access_token,
                     httponly=True,
                     secure=not settings.DEBUG,
                     samesite='Lax',
                     path='/'
                     )

                     response.set_cookie(
                            key='refresh_token',
                            value=response.data.get('refresh'),
                            httponly = True,
                            secure = not settings.DEBUG,
                            samesite = 'Lax',
                            path = '/'
                     )       
            # Remove the token from the response body
              del response.data['access']
              del response.data['refresh']
            
              return response
       

class CustomTokenRefreshView(TokenRefreshView):
       def post(self, request, *args, **kwargs):
              # trying to get the refresh token from the cookie
              refresh_token = request.COOKIES.get('refresh_token')

              if refresh_token:
                     #if it exists , puting it into the reqeust data so the parent class can find it
                     request.data['refresh'] = refresh_token

              # calling the parent login to genereate a new access token
              response = super().post(request,*args,**kwargs)

              if response.status_code == 200:
                     # if successful, set the new access token in a cookie
                     response.set_cookie(
                            key = 'access_token',
                            value = response.data.get('access'),
                            httponly=True,
                            secure=not settings.DEBUG,
                            samesite = "Lax",
                            path= '/'
                     )
                     del response.data['access']
              
              return response




class ActiveSessionView(APIView):
       permission_classes = [IsAuthenticated]

       def get(self, request, *args, **kwargs):
              try:
                     active_sessions = get_user_active_sessions(request.user)   # Django will return a list contianing every single refresh token
                     
                     response_data = [dataclasses.asdict(session) for session in active_sessions]

                     return Response(response_data)
              except Exception as e:
                     return error_response(message="No ActiveSession Found",status_code=404,log_message=f"Error in ActiveSessionView : {e}")


class RevokedDevicesView(APIView):

       permission_classes = [IsAuthenticated]

       def post(self, request, *args, **kwargs):
              
              token_jti = request.data.get('jti')

              try:
                     revoke_device_access(request.user, token_jti)
                     return success_response(message="Logout Success from the device")

              except ValueError as e:
                     return error_response(message=str(e),status_code=400)
              
              except Exception as e:
                     return error_response(message="Session not found or already logged out",status_code=404, log_message=f"Error in RevokedDevicesView: {e}")