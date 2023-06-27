from django.conf.urls import include
from django.urls import re_path


urlpatterns = [
    re_path(r"^ext/api/v2/", include("temba.ext.api.v2.urls")),
]
