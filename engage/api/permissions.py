from rest_framework.permissions import BasePermission


class SSLPermission(BasePermission):  # pragma: no cover
    def has_permission(self, request, view):
        return True
