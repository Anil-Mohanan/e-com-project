from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [    
    path('admin/', admin.site.urls),
    
    # 1. Auth URLs (Register, Logout, Password Reset)
    path('api/v1/auth/', include('user_auth.urls')),

    # 2. Login URLs (The ones you thought were missing!)
    # path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 3. App URLs
    path('api/v1/products/', include('product.urls')),
    path('api/v1/orders/', include('orders.urls')),
    path('api/v1/payments/',include('payments.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)