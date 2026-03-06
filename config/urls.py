from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
from django.conf import settings
from django.conf.urls.static import static 

allowed_versions = settings.REST_FRAMEWORK.get('ALLOWED_VERSIONS',['v1'])

version_str = '|'.join(allowed_versions)

api_prefix = rf'^api/(?P<version>({version_str}))/'

urlpatterns = [    
    path('admin/', admin.site.urls),
    
    # 1. Auth URLs (Register, Logout, Password Reset)
    re_path(f'{api_prefix}auth/', include('user_auth.urls')),

    # 2. Login URLs (The ones you thought were missing!)
    # path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 3. App URLs
    re_path(f'{api_prefix}', include('product.urls')),
    re_path(f'{api_prefix}', include('orders.urls')),
    re_path(f'{api_prefix}payments/',include('payments.urls')),
    re_path(f'{api_prefix}analytics/', include('analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)