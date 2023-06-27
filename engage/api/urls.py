from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from .views import AttachmentsEndpoint


urlpatterns = (
    re_path(r"^attachments$", AttachmentsEndpoint.as_view(), name="api.v2.attachments"),
)
urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "api"])
