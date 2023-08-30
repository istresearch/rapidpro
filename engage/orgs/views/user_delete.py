import logging

from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import MonkeyPatcher

from temba.orgs.views import UserCRUDL


class UserViewDeleteOverride(MonkeyPatcher):
    patch_class = UserCRUDL.Delete

    fields = ("id",)
    permission = "auth.user_update"

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger()

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
        from django.http import HttpResponse
        return HttpResponse(
            f"{username} deleted successfully.",
            headers={
                "temba-success": reverse("orgs.user_list"),
            }
        )
    #enddef post

#endclass UserViewDeleteOverride
