from rest_framework import permissions

class IsSellerOrAdmin(permissions.BasePermission):
       def has_permission(self, request, view):
              if request.method in permissions.SAFE_METHODS:#Allow any One to view
                     return True
              if not request.user  or not request.user.is_authenticated:
                     return False
              return request.user.is_superuser or getattr(request.user, 'is_seller', False)
       def has_object_permission(self, request, view, obj):
              #Allow anyone to View
              if request.method in permissions.SAFE_METHODS:
                     return True
              
              #Admins can do anything
              if request.user.is_superuser:
                     return True
              
              return getattr(request.user, 'is_seller',False)
              
              
