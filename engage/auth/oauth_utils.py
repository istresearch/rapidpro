from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import RedirectView


def oauth_username_is_email( claims ):
    return claims.get('email', '')
#enddef oauth_username_is_email

class SsoSignin(RedirectView):
    def get(self, request, **kwargs):
        if request and settings.OAUTH2_CONFIG.is_enabled:
            settings.OAUTH2_CONFIG.is_logged_in = ( request.user is not None )
        #endif
        return redirect(reverse("msgs.msg_inbox"))
    #enddef get
#enddef SooSignin

@method_decorator(login_required, name='dispatch')
class ResetCredential(RedirectView):

    def get(self, request, **kwargs):
        logout(request)
        if settings.OAUTH2_CONFIG.is_enabled:
            if settings.OAUTH2_CONFIG.is_logged_in:
                return redirect(settings.OAUTH2_CONFIG.get_logout_url())
            #endif
        #endif OAUTH2_PROVIDER is enabled
    #enddef get
#endclass ResetCredential
