from django.conf import settings
from django.conf.urls import include, url


urlpatterns = [
]

if settings.OAUTH2_CONFIG:
    urlpatterns.append(
        url(r"^oidc/", include('oauth2_provider.urls', namespace='oauth2_provider')),
    )

    #from .oauth_utils import ResetCredential

#endif OAUTH2_CONFIG exists
