from django.urls import path,include
from .views import RegisterView,LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name= 'register'),
    path('password_reset/',include('django_rest_passwordreset.urls',namespace='password_reset')),
    path('logout/', LogoutView.as_view(), name='logout'),
]
