import json
import logging
import requests
import ssl
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from temba.api.v2.views_base import BaseAPIView
from temba.orgs.views import OrgPermsMixin

from engage.api.permissions import SSLorLocalTrafficPermission
from engage.api.responses import HttpResponseNoContent
from engage.utils import get_required_arg
from engage.utils.logs import LogExtrasMixin
from engage.utils.pm_config import PMConfig
from engage.utils.ssl_adapter import TLSAdapter
from engage.utils.strings import is_empty


logger = logging.getLogger()

class APIsForDownloadPostmaster(LogExtrasMixin):
    """
    Endpoints and methods used to enable short-lived public download links as
    well as protected long-lived links.
    """

    pm_config: Optional[PMConfig] = None
    log_extras: dict = {
        'slug': settings.DEFAULT_BRAND_OBJ['slug'],
        'version': settings.DEFAULT_BRAND_OBJ['version'],
    }

    @classmethod
    def get_actions(cls):
        return (
            "postmaster_info",
            "download_postmaster",
        )
    #enddef get_actions

    class PostmasterInfo(LogExtrasMixin, OrgPermsMixin, BaseAPIView):
        """
        Endpoint for non-public access for PO to get apk info and download link.
        """
        permission_classes = (SSLorLocalTrafficPermission,)
        permission = "apks.apk_list"

        def __init__(self):
            super().__init__()
            self.pm_config: PMConfig = settings.PM_CONFIG
            self.log_extras = {
                'slug': settings.DEFAULT_BRAND_OBJ['slug'],
                'version': settings.DEFAULT_BRAND_OBJ['version'],
                'endpoint': self.__class__.__name__,
            }
        #enddef init

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r"^pm/info/?$"
        #enddef derive_url_pattern

        def get(self, request: HttpRequest, *args, **kwargs):
            user = self.get_user()
            #logger.debug("user?", extra=self.with_log_extras({
            #    'req.user': request.user if hasattr(request, 'user') else None,
            #    'user': user,
            #}))
            if not user.is_authenticated or user is AnonymousUser:
                return HttpResponseNoContent('Not authorized', status=401)
            if not user.is_allowed(self.permission):
                return HttpResponseNoContent('Forbidden', status=403)
            try:
                pm_info = self.pm_config.fetch_apk_link()
                if pm_info:
                    the_nonce = settings.PM_CONFIG.get_nonce()
                    response_payload = pm_info.copy()
                    response_payload['link'] = settings.HOST_ORIGIN + reverse('channels.channel_download_postmaster',
                        args=(the_nonce,),
                    )
                    r = HttpResponse(json.dumps(response_payload), content_type='application/json')
                    return r
                else:
                    return HttpResponse('resource not found', status=404)
                #endif
            except ValueError as vx:
                return HttpResponse(vx, status=500)
            #endtry
        #enddef get

        def post(self, request, *args, **kwargs):
            return self.get(request, args, kwargs)
        #enddef post

    #endclass PostmasterInfo

    class DownloadPostmaster(LogExtrasMixin, OrgPermsMixin, BaseAPIView):
        """
        Endpoint for public access via random short-lived UUID in URL path to download pm APK.
        """
        permission_classes = (SSLorLocalTrafficPermission,)
        permission = "apks.apk_list"

        def __init__(self):
            super().__init__()
            self.pm_config: PMConfig = settings.PM_CONFIG
            self.log_extras = {
                'slug': settings.DEFAULT_BRAND_OBJ['slug'],
                'version': settings.DEFAULT_BRAND_OBJ['version'],
                'endpoint': self.__class__.__name__,
            }
        #enddef init

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r"^pm/dl-apk/(?P<url_nonce>[^/]+)/?$"
        #enddef derive_url_pattern

        def get(self, request: HttpRequest, *args, **kwargs):
            if not is_empty(self.pm_config.fetch_url):
                theNonce = get_required_arg('url_nonce', kwargs)
                try:
                    if self.pm_config.validate_nonce(theNonce):
                        return self.doDownload(request)
                    else:
                        return HttpResponse('resource not found', status=404)
                except TypeError:
                    # special endpoint that requires auth
                    user = self.get_user()
                    #logger.debug("user?", extra=self.with_log_extras({
                    #    'req.user': request.user if hasattr(request, 'user') else None,
                    #    'user': user,
                    #}))
                    if not user.is_authenticated or user is AnonymousUser:
                        return HttpResponseNoContent('Not authorized', status=401)
                    if user.is_allowed(APIsForDownloadPostmaster.PostmasterInfo.permission):
                        return self.doDownload(request)
                    else:
                        return HttpResponseNoContent(status=403)
                    #endif
                #endtry
            else:
                logger.warning("POST_MASTER_FETCH_URL not defined", extra=self.with_log_extras({}))
                return HttpResponse('resource not found', status=404)
            #endif pm fetch url defined
        #enddef dispatch

        def doDownload(self, request: HttpRequest):
            apk_content_type = 'application/vnd.android.package-archive'
            try:
                if not self.pm_config.pm_info:
                    self.pm_config.fetch_apk_link()
                if self.pm_config.pm_info:
                    pm_link = self.pm_config.pm_info['link']
                    pm_filename = self.pm_config.pm_info['filename']
                    pm_version = self.pm_config.pm_info['version']

                    resp = requests.get(pm_link, auth=self.pm_config.fetch_auth, timeout=60)
                    if resp is not None and resp.ok:
                        r = HttpResponse(resp.content, content_type=apk_content_type)
                        r["Content-Disposition"] = f"attachment; filename={pm_filename}"
                        return r
                    #endif
                else:
                    logger.warning("pm not found", extra=self.with_log_extras({
                        'pm_info': self.pm_config.pm_info,
                    }))
                    return HttpResponse('resource not found', status=404)
                #endif
            except ValueError as vx:
                return HttpResponse(vx, status=500)
            #endtry
        #enddef get

    #endclass DownloadPostmaster

#endclass APIsForDownloadPostmaster
