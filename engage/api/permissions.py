import logging
from django.http import HttpRequest
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class SSLorLocalTrafficPermission(BasePermission):  # pragma: no cover
    """
    Verifies that the requestor is either using HTTPS or is a local requestor.
    """
    logger = logging.getLogger(__name__)

    def has_permission(self, request: Request, view):
        req: HttpRequest = request._request
        self.logger.debug("[TRACE] ssl or local has_perm", extra={
            'req': request,
            'is_sec': req.is_secure(),
            'host': req.get_host(),
            'scheme': req.scheme,
            'hdrs': req.headers,
            'meta': req.META,
            'view': view,
        })
        return True
    #enddef has_permission

#endclass SSLorLocalTrafficPermission

class SiteAdminPermission(BasePermission):
    """
    Verifies that the user is a site-admin.
    """

    def has_permission(self, request, view):
        return request.user.is_superuser
    #enddef has_permission

#endclass SiteAdminPermission
