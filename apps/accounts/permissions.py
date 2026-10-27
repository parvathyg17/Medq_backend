from rest_framework import permissions


class IsAdminUserRole(permissions.BasePermission):
    """
    Allows access only to users with the ADMIN role or superusers/staff.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser)
        )


class IsDeliveryPersonRole(permissions.BasePermission):
    """
    Allows access to users with the DELIVERY_PERSON or ADMIN role.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role in ['DELIVERY_PERSON', 'ADMIN'] or request.user.is_staff)
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access/edit it,
    unless the requesting user is an admin.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff or (request.user.is_authenticated and request.user.role == 'ADMIN'):
            return True
        return hasattr(obj, 'user') and obj.user == request.user
