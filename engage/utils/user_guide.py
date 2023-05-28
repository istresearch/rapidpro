import logging
from pathlib import Path
from typing import Optional

from django.conf import settings
from django.urls import re_path
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
from rest_framework.views import View

from temba import settings
from temba.orgs.views import OrgPermsMixin

from engage.utils.logs import OrgPermLogInfoMixin
from engage.utils.s3_config import AwsS3Config


class UserGuideMixin:

    @classmethod
    def get_actions(cls):
        return (
            "user_guide",
        )

    class UserGuide(OrgPermLogInfoMixin, OrgPermsMixin, View):  # pragma: no cover

        def __init__(self):
            super().__init__()
            self.s3_config: Optional[AwsS3Config] = None
            self.file_path: Optional[Path] = None
            if settings.USER_GUIDE_CONFIG.is_defined():
                self.s3_config = settings.USER_GUIDE_CONFIG
            elif len(settings.USER_GUIDE_CONFIG.FILEPATH) > 1:
                self.file_path = Path(settings.USER_GUIDE_CONFIG.FILEPATH)
            #endif

        def dispatch(self, request: HttpRequest, *args, **kwargs):
            # non authenticated users without orgs get an error (not the org chooser)
            user = self.get_user()
            if not user.is_authenticated:
                return HttpResponse('Not authorized', status=401)

            return super().dispatch(request, *args, **kwargs)

        def get(self, request: HttpRequest, *args, **kwargs):
            logger = logging.getLogger()

            user = self.get_user()
            if not user or user is AnonymousUser:
                return HttpResponse('Not authorized', status=401)

            try:
                if self.s3_config:
                    s3obj = self.s3_config.get_obj()
                    if s3obj is not None:
                        return HttpResponse(s3obj["Body"], content_type='application/pdf')
                    else:
                        return HttpResponse('file not found', status=404)

                    #TODO: Compressing not neccessary, but may be desired someday; figure out how later.
                    #import io
                    #import gzip
                    #import zipfile
                    #from django.core.handlers.wsgi import WSGIRequest
                    # is_zip = True if request.GET.get('zip', '0') in ['1', 'true', 'True', 'T'] else False
                    # is_gz = True if request.GET.get('gzip', '0') in ['1', 'true', 'True', 'T'] else False
                    # if is_zip: # or request.accepts('zip'):
                    #     buffer = io.BytesIO()
                    #     theZip = zipfile.ZipFile(file=buffer, mode='wb')
                    #     theZip.filename=basename(self.s3_object_path)
                    #     theZip.writestr(data=s3obj["Body"])
                    #     theZip.close()
                    #     return HttpResponse(buffer.getvalue(), content_type='application/zip')
                    # elif is_gz: # or request.accepts('gzip'):
                    #     gz = gzip.GzipFile(filename=self.s3_object_name, fileobj=s3obj["Body"])
                    #     return HttpResponse(gz.read(), content_type='application/gzip')
                    # else:
                    #     return HttpResponse(s3obj["Body"], content_type='application/pdf')
                    # #endif
                elif self.file_path and self.file_path.is_file():
                    return HttpResponse(self.file_path.open(mode='rb'), content_type='application/pdf')
                else:
                    logger.error("user guide: neither S3 nor filepath defined", extra=self.withLogInfo({
                    }))
                    raise ValueError("User Guide config not found.")
                #endif
            except ValueError as vx:
                return HttpResponse(vx, status=500)
            #endtry

        def post(self, request, *args, **kwargs):
            return self.get(request, args, kwargs)

    #endclass UserGuide

#endclass UserGuideMixin

urlpatterns = [
    re_path(
        r"^user_guide$",
        UserGuideMixin.UserGuide.as_view(),
        name="engage.user_guide",
    ),
]
