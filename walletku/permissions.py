from rest_framework.permissions import BasePermission


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        try:
            if request.user.is_anonymous:
                return False
        except AttributeError:
            if request.user:
                return True
        return False
