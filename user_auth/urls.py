from django.urls import path,include
from .views import RegisterView,LogoutView,UserProfileView,DeleteAccountView

urlpatterns = [
    path('register/', RegisterView.as_view(), name= 'register'),
    path('password_reset/',include('django_rest_passwordreset.urls',namespace='password_reset')),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/',UserProfileView.as_view(),name = 'profile'),
    path('delete/', DeleteAccountView.as_view(), name = 'delete_account'),
]
