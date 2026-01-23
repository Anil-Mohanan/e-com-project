from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import UserRegistrationSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterView(generics.CreateAPIView):# using generics for safety reasons , generics only do one specfic method one at a time
       queryset = User.objects.all()
       serializer_class = UserRegistrationSerializer
       permission_classes = [AllowAny]# Anyone must be able to register!