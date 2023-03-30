from rest_framework.urlpatterns import format_suffix_patterns

from django.conf.urls import url

from .views import AttachmentsEndpoint


urlpatterns = (
    url(r"^attachments$", AttachmentsEndpoint.as_view(), name="api.v2.attachments"),
)
urlpatterns = format_suffix_patterns(urlpatterns, allowed=["json", "api"])
