from temba import settings
from django.conf.urls import include, url


urlpatterns = [
]

if settings.OAUTH2_CONFIG.is_enabled:
    urlpatterns.append(
        url(r"^oidc/", include('oauth2_authcodeflow.urls', namespace='oauth2_authcodeflow')),
    )
#endif
