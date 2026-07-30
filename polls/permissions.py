from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom object-level permission to only allow authors of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):

        if request.method == permissions.SAFE_METHODS:
            return True

        return obj.author == request.user
    