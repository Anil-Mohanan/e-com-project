from django.urls import path,include
from .views import RegisterView,LogoutView,UserProfileView,DeleteAccountView,VerifyEmailView,CustomTokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterView.as_view(), name= 'register'),
    path('password_reset/',include('django_rest_passwordreset.urls',namespace='password_reset')),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/',UserProfileView.as_view(),name = 'profile'),
    path('delete/', DeleteAccountView.as_view(), name = 'delete_account'),
    path('verify-email/<uidb64>/<token>/',VerifyEmailView.as_view(),name='verify_email'),
]
