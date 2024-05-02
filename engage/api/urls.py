from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from .endpoint.attachments import AttachmentsEndpoint
from .endpoint.ping import PingEndpoint
from .endpoint.pminfo import PmInfoEndpoint
from .endpoint.pmschemes import PmSchemesEndpoint

urlpatterns = (
    re_path(r"^attachments$", AttachmentsEndpoint.as_view(), name="api.v2.attachments"),
)
urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "api"])
urlpatterns += (
    re_path(r"^ping$", PingEndpoint.as_view(), name="ping"),
    re_path(r"^pmschemes$", PmSchemesEndpoint.as_view(), name="pmschemes"),
    re_path(r"^pminfo$", PmInfoEndpoint.as_view(), name="pminfo"),
)
