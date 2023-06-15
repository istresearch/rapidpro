import django_cache_url
from getenv import env
import logging
import re
import requests
import ssl
from typing import Match, Optional
from urllib.parse import urlparse
from uuid import uuid4

from engage.utils.ssl_adapter import TLSAdapter
from engage.utils.strings import is_empty


logger = logging.getLogger()

class PMConfig:
    """
    Helper class to configure a feature with access to PM download nonce info.
    """

    def __init__(self, REDIS_URL: str, CACHES: dict):
        super().__init__()

        self.fetch_url = env('POST_MASTER_FETCH_URL', None)
        #python request does not handle user:pswd@host
        #self.log_url = re.sub(r'://.+:.+@', '://REDACTED@', self.url) if (not is_empty(self.url) and "@" in self.url) else self.url
        self.auth_user = env('POST_MASTER_FETCH_USER', None)
        self.auth_pswd = env('POST_MASTER_FETCH_PSWD', None)
        self.fetch_auth = (self.auth_user, self.auth_pswd) if not is_empty(self.auth_user) else None
        self.pm_info = None

        self.url_nonce_alias = 'dl-pm-nonces'
        self.url_nonce_prefix = f"{self.url_nonce_alias}"
        self.url_nonce_po_only = env('POST_MASTER_FETCH_NONCE4PO', 'postoffice-only')

        if not is_empty(self.fetch_url) and not is_empty(REDIS_URL):
            CACHES[self.url_nonce_alias] = django_cache_url.parse(REDIS_URL)
            if CACHES[self.url_nonce_alias]['BACKEND'] == 'django_redis.cache.RedisCache':
                CACHES[self.url_nonce_alias].update({
                    'TIMEOUT': 1800,  #in seconds
                    'KEY_PREFIX': self.url_nonce_prefix,
                })
                # if 'OPTIONS' not in CACHES[self.url_nonce_alias]:
                #     CACHES[self.url_nonce_alias]['OPTIONS'] = {}
                # #endif
                # CACHES[self.url_nonce_alias]['OPTIONS'].update({
                #     'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                # })
            #endif
        #endif PM fetch url and redis specified

    #enddef init

    def get_cache(self):
        from django.core.cache import caches
        return caches[self.url_nonce_alias]
    #enddef get_cache

    def get_nonce_value(self):
        return uuid4().hex  #.hex removes the dashes
    #enddef get_nonce_value

    def get_nonce(self):
        theCache = self.get_cache()
        if not theCache:
            return ''
        theNonce = self.get_nonce_value()
        theCache.set(theNonce, True)
        return theNonce
    #enddef get_nonce

    def validate_nonce(self, nonce: str) -> bool:
        """
        Check to see if nonce is in redis cache.
        :param nonce: the nonce to check.
        :return: True|False if nonce is uuid and in cache or not; toss
                 ValueError exception if it is po-only nonce that needs auth.
        """
        if nonce == self.url_nonce_po_only:
            raise TypeError('check auth')

        theCache = self.get_cache()
        if not theCache:
            return False
        theVal = theCache.get(nonce, None) if nonce else None
        return theVal if type(theVal) is bool else False
    #enddef validate_nonce

    def fetch_apk_link(self) -> Optional[dict]:
        """
        Common method to get pm download information. May throw a ValueError.
        :return: dict(link, filename, version)
        """
        if not self.fetch_url:
            return None
        #endif
        #logger.debug("pm fetch_apk_link", extra={
        #    'fetch_url': self.fetch_url,
        #    #'auth': obj.fetch_auth,
        #})
        try:
            resp = requests.get(self.fetch_url, auth=self.fetch_auth, timeout=60)
            self.pm_info = self.parse_fetch_apk_link(resp)
        except Exception as ex:
            logger.warning("pm EX fetch_apk_link", extra={
                'ex': ex,
            })
            raise
        #endtry
        return self.pm_info
    #enddef fetch_apk_link

    def parse_fetch_apk_link(self, resp) -> Optional[dict]:
        if resp is not None and resp.ok:
            ctype = resp.headers.get('Content-Type')
            if ctype is not None and ctype.startswith('text/html'):
                list_of_links = resp.text
                pm_link_match: Optional[Match[str]] = None
                # page may list ordered links, get last one: <a href="pm-4.0.15.alpha.2709.apk">
                for pm_link_match in re.finditer(r'<a href="(.+\.apk)">', list_of_links):
                    pass
                if pm_link_match:
                    pm_filename = pm_link_match.group(1)
                    pm_version = pm_filename[3:-4]
                    if self.fetch_url.endswith('/'):
                        pm_link = self.fetch_url + pm_filename
                    else:
                        pm_link = f"{self.fetch_url}/{pm_filename}"
                    #endif
                    #logger.debug("pm link parse", extra={
                    #    'pm_link': pm_link,
                    #    'pm_filename': pm_filename,
                    #    'pm_version': pm_version,
                    #})
                else:
                    #logger.debug("pm link parse", extra={
                    #    'pm_link': None,
                    #})
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
        else:
            logger.error("pm fetch url failed to fetch apk", extra={
                'url': self.fetch_url,
                'resp': resp,
                'content-type': resp.headers.get('Content-Type') if resp is not None else '',
            })
        #endif
    #enddef parse_fetch_apk_link

    def get_pm_app_version(self) -> str:
        try:
            self.pm_info = self.fetch_apk_link()
            if self.pm_info:
                return self.pm_info['version']
            #endif
        except ValueError as vx:
            logger.error("pm ValueError on get_pm_app_version", extra={
                'ex': vx,
            })
            return str(vx)
        #endtry
    #enddef get_pm_app_version

#endclass PMConfig
