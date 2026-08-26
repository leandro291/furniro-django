from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffAuthor(BasePermission):
    """Lectura pública; escritura solo para staff (autor forzado a request.user)."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
