from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import UserRegistrationSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()

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
                     return Response({"error": "Invalid token"},status=status.HTTP_400_BAD_REQUEST)
                     
