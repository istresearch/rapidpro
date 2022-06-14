from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import RedirectView

@method_decorator(login_required, name='dispatch')
class ResetCredential(RedirectView):

    def get(self, request, **kwargs):
        logout(request)
        if settings.OAUTH2_CONFIG:
            from .oauth_config import OAuthConfig
            oac: OAuthConfig = settings.OAUTH2_CONFIG
            return redirect(oac.get_logout_redirect())
        #endif OAUTH2_PROVIDER exists
    #enddef

#endclass ResetCredential
