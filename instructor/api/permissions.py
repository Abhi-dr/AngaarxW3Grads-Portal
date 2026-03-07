from rest_framework import permissions

class IsInstructor(permissions.BasePermission):
    """
    Custom permission to only allow instructors to access the views.
    Checks if the authenticated user has the role 'instructor' and is_staff is True.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff and
            hasattr(request.user, 'role') and 
            request.user.role == 'instructor'
        )
