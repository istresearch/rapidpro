import io

import boto3
import gzip
import logging
from typing import Optional
import zipfile

from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.models import AnonymousUser, User
#from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpRequest, HttpResponse
from rest_framework.views import View

from temba import settings
from temba.orgs.views import OrgPermsMixin

from engage.utils.logs import OrgPermLogInfoMixin


class UserGuideMixin:

    @classmethod
    def get_actions(cls):
        return (
            "user_guide",
        )

    class UserGuide(OrgPermLogInfoMixin, OrgPermsMixin, View):  # pragma: no cover

        def __init__(self):
            super().__init__()
            self.user: Optional[User] = None
            self.aws_session: Optional[boto3.Session] = None
            self.s3_config: bool = False
            if settings.USER_GUIDE_CONFIG['AWS_S3_BUCKET']:
                self.s3_config = True
                self.s3_bucket: str = settings.USER_GUIDE_CONFIG['AWS_S3_BUCKET']
                self.s3_access_key_id: str = settings.USER_GUIDE_CONFIG['AWS_S3_ACCESS_KEY_ID']
                self.s3_secret_key: str = settings.USER_GUIDE_CONFIG['AWS_S3_SECRET_KEY']
                self.s3_region: str = settings.USER_GUIDE_CONFIG['AWS_S3_REGION']
                self.s3_endpoint_url: str = settings.USER_GUIDE_CONFIG['AWS_S3_ENDPOINT_URL']
                self.s3_object_path: str = settings.USER_GUIDE_CONFIG['AWS_S3_PATH']
                self.s3_object_name: str = settings.USER_GUIDE_CONFIG['FILENAME']
                self.s3_object_key = f"{self.s3_object_path}/{self.s3_object_name}" \
                    if self.s3_object_path else self.s3_object_name
            #endif

        def dispatch(self, request: HttpRequest, *args, **kwargs):
            # non authenticated users without orgs get an error (not the org chooser)
            user = self.get_user()
            if not user.is_authenticated:
                return HttpResponse('Not authorized', status=401)

            return super().dispatch(request, *args, **kwargs)

        def get(self, request: HttpRequest, *args, **kwargs):
            logger = logging.getLogger(__name__)

            user = self.get_user()
            if not user or user is AnonymousUser:
                return HttpResponse('Not authorized', status=401)

            try:
                if self.s3_config:
                    if self.aws_session is None:
                        self.aws_session = boto3.session.Session(
                            aws_access_key_id=self.s3_access_key_id,
                            aws_secret_access_key=self.s3_secret_key,
                        )
                    #endif

                    if self.s3_endpoint_url:
                        s3client = self.aws_session.client('s3', endpoint_url=self.s3_endpoint_url, region_name=self.s3_region)
                    else:
                        s3client = self.aws_session.client('s3', region_name=self.s3_region)
                    #endif
                    s3obj = s3client.get_object(Bucket=self.s3_bucket, Key=self.s3_object_key)

                    logger.debug("served user guide", extra=self.withLogInfo({
                        'bucket': self.s3_bucket,
                        'filepath': self.s3_object_key,
                    }))
                    return HttpResponse(s3obj["Body"], content_type='application/pdf')

                    #TODO: Compressing not neccessary, but may be desired someday; figure out how later.
                    # is_zip = True if request.GET.get('zip', '0') in ['1', 'true', 'True', 'T'] else False
                    # is_gz = True if request.GET.get('gzip', '0') in ['1', 'true', 'True', 'T'] else False
                    # if is_zip: # or request.accepts('zip'):
                    #     buffer = io.BytesIO()
                    #     theZip = zipfile.ZipFile(file=buffer, mode='wb')
                    #     theZip.filename=self.s3_object_name
                    #     theZip.writestr(data=s3obj["Body"])
                    #     theZip.close()
                    #     return HttpResponse(buffer.getvalue(), content_type='application/zip')
                    # elif is_gz: # or request.accepts('gzip'):
                    #     gz = gzip.GzipFile(filename=self.s3_object_name, fileobj=s3obj["Body"])
                    #     return HttpResponse(gz.read(), content_type='application/gzip')
                    # else:
                    #     return HttpResponse(s3obj["Body"], content_type='application/pdf')
                    # #endif
                else:
                    logger.error("user guide S3 not defined", extra=self.withLogInfo({
                    }))
                    raise ValueError("User Guide S3 config not found.")
                #endif
            except ValueError as vx:
                return HttpResponse(vx, status=500)
            #endtry

        def post(self, request, *args, **kwargs):
            return self.get(request, args, kwargs)

    #endclass UserGuide

#endclass UserGuideMixin

urlpatterns = [
    url(
        r"^user_guide$",
        UserGuideMixin.UserGuide.as_view(),
        name="engage.user_guide",
    ),
]
