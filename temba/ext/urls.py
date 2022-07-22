from django.conf.urls import include, url


urlpatterns = [
    url(r"^ext/api/v2/", include("temba.ext.api.v2.urls")),
]
