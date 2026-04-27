from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import update_last_login
from user_auth.models import UserDeviceSession
User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
       # write_only menas the password is never going to send back to them 
       password = serializers.CharField(write_only=True)# very important
       full_name = serializers.CharField(write_only= True, required = False)
       class Meta:
              model = User
              fields = ['email','password','full_name']
              
       def validate_password(self,value):
              validate_password(value)
              return value
       
       def validate_full_name(self, value):
              if "<" in value or ">" in value:
                     raise serializers.ValidationError("Full Name cannot contain HTML Pages")
              return value
       
       def create(self, validated_data):
              full_name = validated_data.get('full_name','')
              parts = full_name.split(' ',1)
              first_name = parts[0]
              last_name = parts[1] if len(parts) > 1 else ''
              
              user = User.objects.create_user(
                     email  = validated_data ['email'],
                     password=validated_data['password'],
                     first_name = first_name,
                     last_name = last_name,
                     is_customer = validated_data.get('is_customer',True),
                     is_seller= validated_data.get('is_seller',False),
                     
              )
              return user
class UserSerializer(serializers.ModelSerializer):
       class Meta:
              model = User       
              fields = ['id','username', 'email', 'first_name', 'last_name','is_customer','is_seller','is_staff','date_joined']
              
              read_only_fields = ['id','email','is_customer','is_seller','is_staff','date_joined']
              

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
       def validate(self, attrs):
              
              data = super().validate(attrs)

              if not self.user.is_email_verified:
                     raise AuthenticationFailed("Email is not verified. Please verify you email ")

              request = self.context.get('request')
              refresh = RefreshToken(data['refresh']) # passing the raw refresh token back to refresh token class for to decode it 
              new_jti = refresh['jti'] # Extracting the unique jit the serial number from the refresh token 
              
              x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')#  HTTP_X_FORWARDED_FOR Header contain the real use ip 

              if x_forwarded_for: 
                     ip = x_forwarded_for.split(',')[0]
              else:
                     ip = request.META.get('REMOTE_ADDR') # Django normaly store the IP address in the Header "REMOTE_ADDR"

              device = request.META.get('HTTP_USER_AGENT','Unknown Device') # The WebBrowswer header "HTTP_USER_AGENT"

              UserDeviceSession.objects.create( # Saving it into the DB
                     user = self.user,
                     jti = new_jti,
                     ip_address = ip,
                     device_name = device
              )
              return data
       @classmethod
       def get_token(cls,user):
              # Token Versioning
              token = super().get_token(user)
              token['is_customer'] = user.is_customer
              token['is_seller'] = user.is_seller
              token['jwt_version'] = user.jwt_version

              return token