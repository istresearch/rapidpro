from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from engage.utils.class_overrides import MonkeyPatcher

from temba.api.support import APITokenAuthentication


class APITokenAuthenticationOverride(MonkeyPatcher):
    patch_class = APITokenAuthentication

    def authenticate(self, request):
        user, token = self.super_authenticate(request)
        if ( settings.MAUTH_DOMAIN and request.is_secure() ):
            org = user.get_org() if user.is_authenticated else None
            if org and org.config and org.config.get('mauth_enabled', 0):
                if not ( 'X-Forwarded-Host' in request.headers
                    and request.headers.get('X-Forwarded-Host') == settings.MAUTH_DOMAIN
                ):
                    raise AuthenticationFailed("Forbidden")
                #endif did not use the mauth domain
            #endif org is configured for mauth
        #endif mauth configured and used a token as auth
        return user, token
    #enddef authenticate

#endclass APITokenAuthenticationOverride
