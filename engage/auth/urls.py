from django.conf.urls import include, url

from temba import settings

urlpatterns = [
]

if settings.KEYCLOAK_URL:
    urlpatterns.append(
        url(r"^oidc/", include('oauth2_provider.urls', namespace='oauth2_provider')),
    )
#endif
