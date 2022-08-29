import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.orgs.views import UserCRUDL

class UserViewDeleteOverride(ClassOverrideMixinMustBeFirst, UserCRUDL.Delete):
    fields = ("id",)
    permission = "auth.user_update"

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)

        user = self.get_object()
        username = user.username
        logger.info("delete user", extra={
            'user_id': user.id,
            'user_name': username,
            'user_email': user.email,
            'fn': user.first_name,
            'ln': user.last_name,
        })

        brand = self.request.branding.get("brand")
        user.release(self.request.user, brand=brand)

        messages.success(self.request, _(f"Deleted user {username}"))
        return HttpResponseRedirect(reverse("orgs.user_list", args=()))
    #enddef post

#endclass UserViewDeleteOverride