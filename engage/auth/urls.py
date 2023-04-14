from temba import settings
from django.conf.urls import include
from django.urls import re_path
from .oauth_utils import SsoSignin


urlpatterns = [
]

if settings.OAUTH2_CONFIG.is_enabled:
    urlpatterns += (
        re_path(r"^oidc/", include('oauth2_authcodeflow.urls')),
        re_path(r"^sso_signin$", SsoSignin.as_view(), name="engage.sso_signin"),
    )
#endif
