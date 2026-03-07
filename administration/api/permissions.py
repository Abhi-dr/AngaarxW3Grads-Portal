from rest_framework import permissions

class IsAdministrator(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff and
            hasattr(request.user, 'role') and 
            request.user.role == 'admin'
        )

class IsAdministratorOrInstructor(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff and
            hasattr(request.user, 'role') and 
            request.user.role in ['admin', 'instructor']
        )
