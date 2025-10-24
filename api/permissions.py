from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapped_view(self, request, *args, **kwargs):
            user_roles = set()
            if request.user.groups.filter(name='Admin').exists() or request.user.is_superuser:
                user_roles.add('Admin')
            if request.user.groups.filter(name='Librarian').exists():
                user_roles.add('Librarian')
            if request.user.groups.filter(name='Member').exists():
                user_roles.add('Member')
            
            if not user_roles.intersection(set(allowed_roles)):
                raise PermissionDenied("شما دسترسی لازم برای این عملیات را ندارید")
            
            return view_func(self, request, *args, **kwargs)
        return wrapped_view
    return decorator

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Admin').exists() or request.user.is_superuser

class IsLibrarian(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Librarian').exists()

class IsMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Member').exists()
    
class IsLibrarianOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return (
            user.groups.filter(name='Librarian').exists()
            or user.groups.filter(name='Admin').exists()
            or user.is_superuser
        )