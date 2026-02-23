from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

class CaseInsensitiveModelBackend(ModelBackend):
       def authenticate(self, request, email = None, password = None, **kwargs):
              UserModel = get_user_model()

              if email is None:
                     email = kwargs.get(UserModel.USERNAME_FIELD)
              try:
                     user = UserModel.objects.get(email__iexact= email) # The 'iexact' tells Django: "Find this email regardless of capital letters"
              except UserModel.DoesNotExist:
                     return None
              
              if user.check_password(password) and self.user_can_authenticate(user):
                     return user
              return None

class CustomJWTAuthentication(JWTAuthentication):

       def get_user(self, validated_token):

              user = super().get_user(validated_token)

              token_version = validated_token.get('jwt_version')

              if token_version != user.jwt_version:
                     raise AuthenticationFailed("Toke is invalid")

              return user


       