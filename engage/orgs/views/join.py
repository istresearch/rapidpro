from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from temba.orgs.views import OrgCRUDL
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib import messages
from temba.orgs.models import User as TembaUser

from django.conf import settings

from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.logs import LogExtrasMixin


class JoinOverrides(MonkeyPatcher, LogExtrasMixin):
    patch_class = OrgCRUDL.Join

    def pre_process(self, request, *args, **kwargs):
        secret = self.kwargs.get("secret")

        invite = self.get_invitation()
        if invite:
            has_user = TembaUser.objects.filter(username=invite.email, is_active=True).exists()

            if has_user:
                join_accept_url = reverse("orgs.org_join_accept", args=[secret])
                if invite.email == request.user.username:
                    return HttpResponseRedirect(join_accept_url)
                elif settings.OAUTH2_CONFIG.is_enabled:
                    return HttpResponseRedirect(settings.OAUTH2_CONFIG.get_login_url(join_accept_url))

            logout(request)
            if not has_user:
                return HttpResponseRedirect(reverse("orgs.org_create_login", args=[secret]))

        else:
            messages.info(
                request, _("Your invitation link has expired. Please contact your workspace administrator.")
            )
            return HttpResponseRedirect(reverse("users.user_login"))

