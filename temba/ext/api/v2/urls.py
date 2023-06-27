from django.urls import re_path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import ExtChannelsEndpoint, ExtStatusEndpoint


urlpatterns = [
    re_path(r"^channels$", ExtChannelsEndpoint.as_view(), name="ext.api.v2.channels"),
    re_path(r"^channel/status$", ExtStatusEndpoint.as_view(), name="ext.api.v2.channel.status"),
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "api"])
