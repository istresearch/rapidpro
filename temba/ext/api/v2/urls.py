from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from .views import ExtChannelsEndpoint, ExtStatusEndpoint


urlpatterns = [
    url(r"^channels$", ExtChannelsEndpoint.as_view(), name="ext.api.v2.channels"),
    url(r"^channel/status$", ExtStatusEndpoint.as_view(), name="ext.api.v2.channel.status"),
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "api"])
