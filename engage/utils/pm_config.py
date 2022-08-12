import django_cache_url
from getenv import env
from uuid import uuid4

from engage.utils.strings import is_empty


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

        self.url_nonce_alias = 'dl-pm-nonces'
        self.url_nonce_prefix = f"{self.url_nonce_alias}"
        self.url_nonce_po_only = 'postoffice-only'

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

#endclass PMConfig
