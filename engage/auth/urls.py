from temba import settings
from django.conf.urls import include, url
from .oauth_utils import SsoSignin


urlpatterns = [
]

if settings.OAUTH2_CONFIG.is_enabled:
    urlpatterns += (
        url(r"^oidc/", include('oauth2_authcodeflow.urls')),
        url(r"^sso_signin$", SsoSignin.as_view(), name="engage.sso_signin"),
    )
#endif
