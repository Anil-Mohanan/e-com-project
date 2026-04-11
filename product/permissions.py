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
              is_seller = getattr(request.user,'is_seller',False)       
              if not is_seller:
                     return False
              
              if hasattr(obj,'seller'): # Dynamic Ownership RBAC Routing
                     # It's a Product
                     return obj.seller == request.user
              elif hasattr(obj,'product') and hasattr(obj.product,'seller'):

                     return obj.product.seller == request.user

              return False
       
class IsReviewAuthorOrReadOnly(permissions.BasePermission):
       """Object-level permission to only allow owners of a review to edit/delete it."""
       def has_object_permission(self, request, view, obj):
              # Read permissions are allowed to any request, 
              # always allow GET, HEAD OR OPTION requests.
              if request.method in permissions.SAFE_METHODS:
                     return True
              
              return obj.user == request.user or request.user.is_staff
              #Write permissions (PUT, PATCH, DELETE) are only allow to:
              #the author or the revewi(obj.user == request.user)
              #or an Admin (request.user.is_staff)
              
                     
              
