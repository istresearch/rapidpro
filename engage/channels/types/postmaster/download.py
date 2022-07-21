import logging
import re
import requests
from typing import Match, Optional
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
from rest_framework.views import View

from temba import settings
from temba.orgs.views import OrgPermsMixin

from engage.utils.strings import is_empty
from engage.utils.logs import OrgPermLogInfoMixin


class DownloadPostmasterMixin:

    @classmethod
    def get_actions(cls):
        return (
            "download_postmaster",
        )

    class DownloadPostmaster(OrgPermLogInfoMixin, OrgPermsMixin, View):  # pragma: no cover

        def __init__(self):
            super().__init__()
            self.fetch_url = settings.POST_MASTER_FETCH_URL
            #python request does not handle user:pswd@host
            #self.log_url = re.sub(r'://.+:.+@', '://REDACTED@', self.url) if (not is_empty(self.url) and "@" in self.url) else self.url
            self.auth_user = settings.POST_MASTER_FETCH_USER
            self.auth_pswd = settings.POST_MASTER_FETCH_PSWD
            self.fetch_auth = (self.auth_user, self.auth_pswd) if not is_empty(self.auth_user) else None
        #enddef init

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r"^dl-pm/$"
        #enddef derive_url_pattern

        def dispatch(self, request: HttpRequest, *args, **kwargs):
            # non authenticated users without orgs get an error (not the org chooser)
            user = self.get_user()
            if not user.is_authenticated:
                return HttpResponse('Not authorized', status=401)
            #endif
            return super().dispatch(request, *args, **kwargs)
        #enddef dispatch

        def get(self, request: HttpRequest, *args, **kwargs):
            logger = logging.getLogger(__name__)

            user = self.get_user()
            if not user or user is AnonymousUser:
                return HttpResponse('Not authorized', status=401)

            if not is_empty(self.fetch_url):
                apk_content_type = 'application/vnd.android.package-archive'
                try:
                    resp: requests.Response = requests.get(self.fetch_url, auth=self.fetch_auth)
                    logger.debug("pm fetch url", extra=self.withLogInfo({
                        'url': self.fetch_url,
                        'resp': resp,
                        'content-type': resp.headers.get('Content-Type') if resp is not None else '',
                    }))
                    if resp is not None and resp.ok:
                        ctype = resp.headers.get('Content-Type')
                        if ctype is not None and ctype.startswith('text/html'):
                            list_of_links = resp.text
                            logger.debug("pm fetch list", extra=self.withLogInfo({
                                'list': list_of_links,
                            }))
                            pm_link_match: Optional[Match[str]] = None
                            # page may list ordered links, get last one: <a href="postmaster-4.0.15.alpha.2709.apk">
                            for pm_link_match in re.finditer(r'<a href="(.+\.apk)">', list_of_links):
                                pass
                            logger.debug("pm link parse", extra=self.withLogInfo({
                                'pm_link': pm_link_match.group(1) if pm_link_match else None,
                            }))
                            if pm_link_match:
                                pm_filename = pm_link_match.group(1)
                                if self.fetch_url.endswith('/'):
                                    pm_link = self.fetch_url + pm_filename
                                else:
                                    pm_link = f"{self.fetch_url}/{pm_filename}"
                                #endif
                                resp = requests.get(pm_link, auth=self.fetch_auth)
                                if resp is not None and resp.ok:
                                    r = HttpResponse(resp.content, content_type=apk_content_type)
                                    r["Content-Disposition"] = f"attachment; filename={pm_filename}"
                                    return r
                                #endif
                            #endif
                        else:
                            pm_filename = urlparse(self.fetch_url).path.rsplit('/', 1)[-1]
                            r = HttpResponse(resp.content, content_type=apk_content_type, as_attachment=True, filename=pm_filename)
                            r["Content-Disposition"] = f"attachment; filename={pm_filename}"
                            return r
                        #endif
                    #endif
                    logger.error("pm fetch url failed to fetch apk", extra=self.withLogInfo({
                        'url': self.fetch_url,
                        'resp': resp,
                        'content-type': resp.headers.get('Content-Type') if resp is not None else '',
                    }))
                    return HttpResponse('file not found', status=404)
                except ValueError as vx:
                    return HttpResponse(vx, status=500)
                #endtry
            else:
                logger.warning("POST_MASTER_FETCH_URL not defined", extra=self.withLogInfo({
                }))
                raise ValueError("file not found.")
            #endif
        #enddef get

        def post(self, request, *args, **kwargs):
            return self.get(request, args, kwargs)
        #enddef post

    #endclass DownloadPostmaster

#endclass DownloadPostmasterMixin
