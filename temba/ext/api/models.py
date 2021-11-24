import hmac
import logging
import uuid
from datetime import timedelta
from hashlib import sha1

from rest_framework.permissions import BasePermission
from smartmin.models import SmartModel

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from temba.api.models import APIPermission, APIToken
from temba.orgs.models import Org
from temba.utils.cache import get_cacheable_attr
from temba.utils.models import JSONAsTextField

logger = logging.getLogger(__name__)


class ExtAPIPermission(APIPermission):
    """
    Verifies that the user has the permission set on the endpoint view
    """

    def has_permission(self, request, view):
        return request.user.is_superuser

