from temba import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import RedirectView

@method_decorator(login_required, name='dispatch')
class ResetCredential(RedirectView):

    def get(self, request, **kwargs):
        logout(request)
        if settings.OAUTH2_CONFIG.is_enabled:
            if settings.OAUTH2_CONFIG.is_logged_in:
                return redirect(settings.OAUTH2_CONFIG.get_logout_url())
            #endif
        #endif OAUTH2_PROVIDER is enabled
    #enddef

#endclass ResetCredential
