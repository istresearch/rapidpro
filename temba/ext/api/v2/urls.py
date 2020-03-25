from rest_framework.urlpatterns import format_suffix_patterns

from django.conf.urls import url

from temba.ext.api.v2.views import ExtChannelsEndpoint

urlpatterns = [
    url(r"^channels$", ExtChannelsEndpoint.as_view(), name="ext.api.v2.channels")
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "api"])
