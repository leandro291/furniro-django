from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    """El objeto solo es accesible para el usuario dueño (obj.user)."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id
