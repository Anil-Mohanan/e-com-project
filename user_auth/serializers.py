from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
       # write_only menas the password is never going to send back to them 
       password = serializers.CharField(write_only=True)# very important

       class Meta:
              model = User
              fields = ['email', 'password', 'is_customer', 'is_seller']
       def create(self, validated_data):
              user = User.objects.create_user(
                     email  = validated_data ['email'],
                     password=validated_data['password'],
                     is_customer = validated_data.get('is_customer',True),
                     is_seller= validated_data.get('is_seller',False)

              )
              return user
class UserSerializer(serializers.ModelSerializer):
       class Meta:
              model = User       
              fields = ['id','username', 'email', 'first_name', 'last_name']
              read_only_fields = ['id','email']
       
