import json
import logging
import re
import requests
from typing import Match, Optional, Union
from urllib.parse import urlparse

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
            self.fetch_url = self.pm_config.fetch_url
            self.fetch_auth = self.pm_config.fetch_auth
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
            logger.debug("user?", extra=self.with_log_extras({
                'req.user': request.user if hasattr(request, 'user') else None,
                'user': user,
            }))
            if not user.is_authenticated or user is AnonymousUser:
                return HttpResponseNoContent('Not authorized', status=401)
            if not user.is_allowed(self.permission):
                return HttpResponseNoContent('Forbidden', status=403)
            try:
                pm_info = APIsForDownloadPostmaster.fetch_apk_link(self)
                if pm_info:
                    pm_info['link'] = request.build_absolute_uri(reverse('channels.channel_download_postmaster',
                        args=(self.pm_config.url_nonce_po_only,),
                    ))
                    r = HttpResponse(json.dumps(pm_info), content_type='application/json')
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
            self.fetch_url = self.pm_config.fetch_url
            self.fetch_auth = self.pm_config.fetch_auth
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
                    logger.debug("user?", extra=self.with_log_extras({
                        'req.user': request.user if hasattr(request, 'user') else None,
                        'user': user,
                    }))
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
                pm_info = APIsForDownloadPostmaster.fetch_apk_link(self)
                if pm_info:
                    pm_link = pm_info['link']
                    pm_filename = pm_info['filename']
                    #pm_version = pm_info['version']
                    resp = requests.get(pm_link, auth=self.fetch_auth)
                    if resp is not None and resp.ok:
                        r = HttpResponse(resp.content, content_type=apk_content_type)
                        r["Content-Disposition"] = f"attachment; filename={pm_filename}"
                        return r
                    #endif
                else:
                    return HttpResponse('resource not found', status=404)
                #endif
            except ValueError as vx:
                return HttpResponse(vx, status=500)
            #endtry
        #enddef get

    #endclass DownloadPostmaster

    @staticmethod
    def fetch_apk_link(self: Union[PostmasterInfo, DownloadPostmaster]) -> Optional[dict]:
        """
        Common method to get pm download information. May throw a ValueError.
        :param self: pass in the object which should be used as "self" here.
        :return: dict(link, filename, version)
        """
        resp: requests.Response = requests.get(self.fetch_url, auth=self.fetch_auth)
        if resp is not None and resp.ok:
            ctype = resp.headers.get('Content-Type')
            if ctype is not None and ctype.startswith('text/html'):
                list_of_links = resp.text
                pm_link_match: Optional[Match[str]] = None
                # page may list ordered links, get last one: <a href="pm-4.0.15.alpha.2709.apk">
                for pm_link_match in re.finditer(r'<a href="(.+\.apk)">', list_of_links):
                    pass
                logger.debug("pm link parse", extra=self.with_log_extras({
                    'pm_link': pm_link_match.group(1) if pm_link_match else None,
                }))
                if pm_link_match:
                    pm_filename = pm_link_match.group(1)
                    pm_version = pm_filename[3:-4]
                    if self.fetch_url.endswith('/'):
                        pm_link = self.fetch_url + pm_filename
                    else:
                        pm_link = f"{self.fetch_url}/{pm_filename}"
                    #endif
                else:
                    return None
                #endif
            else:
                pm_link = self.fetch_url
                pm_filename = urlparse(self.fetch_url).path.rsplit('/', 1)[-1]
                pm_version = pm_filename[3:-4]
            #endif
            return {
                'link': pm_link,
                'filename': pm_filename,
                'version': pm_version,
            }
        #endif
        logger.error("pm fetch url failed to fetch apk", extra=self.with_log_extras({
            'url': self.fetch_url,
            'resp': resp,
            'content-type': resp.headers.get('Content-Type') if resp is not None else '',
        }))
        return None
    #enddef fetch_apk_link

#endclass APIsForDownloadPostmaster
