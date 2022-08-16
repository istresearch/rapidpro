# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# -----------------------------------------------------------------------------------
# Engage settings file
# -----------------------------------------------------------------------------------

from getenv import env
from glob import glob
import dj_database_url
import django_cache_url

from engage.auth.oauth_config import OAuthConfig
from engage.utils.strings import is_empty, str2bool
from engage.utils.pm_config import PMConfig
from engage.utils.s3_config import AwsS3Config

from temba.settings_common import *  # noqa

SUB_DIR = env('SUB_DIR', required=False)
# NOTE: we do not support SUB_DIR anymore, kits no longer use it. Feel free to rip out.

COURIER_URL = env('COURIER_URL', 'http://localhost:8080')
DEFAULT_TPS = env('DEFAULT_TPS', 10)    # Default Transactions Per Second for newly create Channels.
MAX_TPS = env('MAX_TPS', 50)            # Max configurable Transactions Per Second for newly Created Channels and Updated Channels.

MAX_ORG_LABELS = int(env('MAX_ORG_LABELS', 500))

POST_OFFICE_QR_URL = env('POST_OFFICE_QR_URL', 'http://localhost:8088/postoffice/engage/claim')
POST_OFFICE_API_KEY = env('POST_OFFICE_API_KEY', 'abc123')

POST_MASTER_DL_URL = env('POST_MASTER_DL_URL', required=False)
POST_MASTER_DL_QRCODE = env('POST_MASTER_DL_QRCODE', required=False)
if POST_MASTER_DL_QRCODE is not None and not POST_MASTER_DL_QRCODE.startswith("data:"):
    POST_MASTER_DL_QRCODE = "data:png;base64, {}".format(POST_MASTER_DL_QRCODE)

MAILROOM_URL=env('MAILROOM_URL', 'http://localhost:8000')

INSTALLED_APPS = (
    tuple(filter(lambda tup : tup not in env('REMOVE_INSTALLED_APPS', '').split(','), INSTALLED_APPS)) + (
        'flatpickr',
        'temba.ext',
        'engage.api',
        'engage.auth',
        'engage.channels',
        'engage.contacts',
        'engage.msgs',
        'engage.orgs',
        'engage.utils',
    ) + tuple(filter(None, env('EXTRA_INSTALLED_APPS', '').split(',')))
)

APP_URLS += (
    'temba.ext.urls',
    'engage.auth.urls',
    'engage.utils.user_guide',
)

TEMPLATES[0]['DIRS'].insert(0,
    os.path.join(PROJECT_DIR, "../engage/hamls"),
)
STATICFILES_DIRS = STATICFILES_DIRS + (
    os.path.join(PROJECT_DIR, "../engage/static"),
    os.path.join(PROJECT_DIR, "../node_config"),
)

ROOT_URLCONF = env('ROOT_URLCONF', 'temba.urls')

DEBUG = env('DJANGO_DEBUG', 'off') == 'on'

# no OSGeo stage building libs, just using pre-built libs now.
# @see https://stackoverflow.com/questions/58403178/geodjango-cant-find-gdal-on-docker-python-alpine-based-image
try:
    GDAL_LIBRARY_PATH = glob('/usr/lib/libgdal.so.*')[0]
    GEOS_LIBRARY_PATH = glob('/usr/lib/libgeos_c.so.*')[0]
except:
    GEOS_LIBRARY_PATH = '/usr/local/lib/libgeos_c.so'
    GDAL_LIBRARY_PATH = '/usr/local/lib/libgdal.so'

SECRET_KEY = env('SECRET_KEY', required=True)

DATABASE_URL = env('DATABASE_URL', required=True)
DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}
DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['ATOMIC_REQUESTS'] = True
DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

REDIS_URL = env('REDIS_URL')
if REDIS_URL:
    BROKER_URL = env('BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', REDIS_URL)
    CACHE_URL = env('CACHE_URL', REDIS_URL)
    CACHES = {'default': django_cache_url.parse(CACHE_URL)}
    if CACHES['default']['BACKEND'] == 'django_redis.cache.RedisCache':
        if 'OPTIONS' not in CACHES['default']:
            CACHES['default']['OPTIONS'] = {}
        CACHES['default']['OPTIONS']['CLIENT_CLASS'] = 'django_redis.client.DefaultClient'


IS_PROD = env('IS_PROD', 'off') == 'on'
# -----------------------------------------------------------------------------------
# Used when creating callbacks for Twilio, Nexmo etc..
# -----------------------------------------------------------------------------------
HOSTNAME = env('DOMAIN_NAME', 'rapidpro.ngrok.com')
TEMBA_HOST = env('TEMBA_HOST', HOSTNAME)

if TEMBA_HOST.lower().startswith('https://') and str2bool(env('USE_SECURE_COOKIES', False)):
    #from .security_settings import *  # noqa
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_AGE = 1209600  # 2 weeks
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_SAMESITE = 'Lax'
#endif

# in order to differentiate "local traffic" vs "external traffic" in k8s,
# we need to utilize x_forwarded_host header and compare it with an expected URL.
HTTP_ALLOWED_URL = None
if not is_empty(env('HTTP_ALLOWED_URL')):
    USE_X_FORWARDED_HOST = True
    HTTP_ALLOWED_URL = env('HTTP_ALLOWED_URL')
#endif

SECURE_PROXY_SSL_HEADER = (env('SECURE_PROXY_SSL_HEADER', 'HTTP_X_FORWARDED_PROTO'), 'https')
INTERNAL_IPS = ('*',)
ALLOWED_HOSTS = env('ALLOWED_HOSTS', HOSTNAME).split(';')

AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', '')
AWS_S3_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', '')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', 'us-east-1')
IS_AWS_S3_REGION_DEFAULT = bool(AWS_S3_REGION_NAME == 'us-east-1')
AWS_SIGNED_URL_DURATION = int(env('AWS_SIGNED_URL_DURATION', '1800'))
AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL', '')
AWS_LOCATION = env('AWS_LOCATION', '')
AWS_QUERYSTRING_EXPIRE = '157784630' #unsure why this is hardcoded as a string
AWS_STATIC = bool(AWS_STORAGE_BUCKET_NAME) and env('AWS_STATIC', False)
AWS_MEDIA = bool(AWS_STORAGE_BUCKET_NAME) and env('AWS_MEDIA', True)
AWS_S3_USE_SSL = bool(env('AWS_S3_USE_SSL', True))
AWS_S3_HTTP_SCHEME = "https" if AWS_S3_USE_SSL else "http"
AWS_S3_VERIFY = env('AWS_S3_VERIFY', False)
AWS_S3_CUSTOM_DOMAIN_NAME = env('AWS_S3_CUSTOM_DOMAIN_NAME', None)
AWS_S3_CUSTOM_URL = env('AWS_S3_CUSTOM_URL', None)

if AWS_STORAGE_BUCKET_NAME:

    if AWS_S3_CUSTOM_URL:
        #TODO FUTURE, IF NEEDED: if there's replacements in string, do them
        AWS_S3_ENDPOINT_URL = AWS_S3_CUSTOM_URL
        AWS_S3_URL = AWS_S3_ENDPOINT_URL
    else:
        if AWS_S3_CUSTOM_DOMAIN_NAME:
            AWS_S3_CUSTOM_DOMAIN = AWS_S3_CUSTOM_DOMAIN_NAME
            AWS_S3_DOMAIN = AWS_S3_CUSTOM_DOMAIN_NAME
        else:
            theRegionDomainSegment = f".{AWS_S3_REGION_NAME}" if not IS_AWS_S3_REGION_DEFAULT else ''
            # middleware still expects us-east-1 in special domain format with bucket leading the subdomain (legacy format).
            theDefaultRegionDomainSegment = f"{AWS_STORAGE_BUCKET_NAME}." if IS_AWS_S3_REGION_DEFAULT else ''
            # useful to override for local dev and hosts file entries
            #  e.g. 127.0.0.1    s3.dev.nostromo.box
            #       127.0.0.1    s3.us-gov-west-1.dev.nostromo.box
            theBaseDomain = env('AWS_BASE_DOMAIN', 'amazonaws.com')
            # useful for local dev ngnix proxies, eg. 'location ^~ /s3/ {'
            thePathPrefix = env('AWS_S3_PATH_PREFIX', '') # MUST START WITH A SLASH, eg. '/s3'
            AWS_S3_DOMAIN = f"{theDefaultRegionDomainSegment}s3{theRegionDomainSegment}.{theBaseDomain}{thePathPrefix}"

        # middleware still expects us-east-1 in special domain format with bucket leading the subdomain (legacy format).
        theBucketPathSegment = f"/{AWS_STORAGE_BUCKET_NAME}" if not IS_AWS_S3_REGION_DEFAULT else ''
        AWS_S3_URL = f"{AWS_S3_HTTP_SCHEME}://{AWS_S3_DOMAIN}{theBucketPathSegment}"

    # explicity remove any trailing slash
    if AWS_S3_URL.endswith('/'):
        AWS_S3_URL = AWS_S3_URL[:-1]

    # Tell django-storages that when coming up with the URL for an item in S3 storage, keep
    # it simple - just use this domain plus the path. (If this isn't set, things get complicated).
    # This controls how the `static` template tag from `staticfiles` gets expanded, if you're using it.
    # We also use it in the next setting.
    # If we call this setting `AWS_S3_CUSTOM_DOMAIN`, that breaks presigned URLs in
    # django-storages. Use our own setting for the domain instead, which is unknown to
    # django-storages.

    if AWS_STATIC:
        # This is used by the `static` template tag from `static`, if you're using that. Or if anything else
        # refers directly to STATIC_URL. So it's safest to always set it.
        STATIC_URL = AWS_S3_URL

        # Tell the staticfiles app to use S3Boto storage when writing the collected static files (when
        # you run `collectstatic`).
        STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        COMPRESS_STORAGE = STATICFILES_STORAGE

    if AWS_MEDIA:
        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        STORAGE_URL = AWS_S3_URL
        MEDIA_URL = f"{AWS_S3_URL}/media/"

if not AWS_MEDIA:
    STORAGE_URL = MEDIA_URL[:-1]

if not AWS_STATIC:
    # @see whitenoise middleware usage: https://whitenoise.evans.io/en/stable/django.html
    STATICFILES_STORAGE = 'engage.utils.storage.WhiteNoiseStaticFilesStorage'
    # insert just after security middleware (which is at idx 0)
    MIDDLEWARE = MIDDLEWARE[:1] + ('whitenoise.middleware.WhiteNoiseMiddleware',) + MIDDLEWARE[1:]
    WHITENOISE_MANIFEST_STRICT = False

STATIC_ROOT = os.path.join(PROJECT_DIR, "../sitestatic/")

# compress_precompilers used for static LESS files whether or not COMPRESS_ENABLED==True
COMPRESS_PRECOMPILERS = (
    ("text/less", 'lessc --include-path="%s:%s" {infile} {outfile}' % (
        os.path.join(COMPRESS_ROOT, "less"),
        os.path.join(COMPRESS_ROOT, "engage", "less"),
    )),
)

COMPRESS_ENABLED = env('DJANGO_COMPRESSOR', 'on') == 'on'
if COMPRESS_ENABLED:
    COMPRESS_URL = STATIC_URL
    COMPRESS_ROOT = STATIC_ROOT
    #COMPRESS_STORAGE = STATICFILES_STORAGE

COMPRESS_OFFLINE_MANIFEST = f"manifest-{env('VERSION_CI', '1-dev')[:-4]}.json"
# If COMPRESS_OFFLINE is False, compressor will look in COMPRESS_STORAGE for
# previously processed results, but if not found, will create them on the fly
# and save them to use again.
#COMPRESS_OFFLINE = False
COMPRESS_OFFLINE = COMPRESS_ENABLED and (env('DEV_STATIC', 'off') != 'on')

MAGE_AUTH_TOKEN = env('MAGE_AUTH_TOKEN', None)
MAGE_API_URL = env('MAGE_API_URL', 'http://localhost:8026/api/v1')
SEND_MESSAGES = env('SEND_MESSAGES', 'off') == 'on'
SEND_WEBHOOKS = env('SEND_WEBHOOKS', 'off') == 'on'
SEND_EMAILS = env('SEND_EMAILS', 'off') == 'on'
SEND_AIRTIME = env('SEND_AIRTIME', 'off') == 'on'
SEND_CALLS = env('SEND_CALLS', 'off') == 'on'
IP_ADDRESSES = tuple(filter(None, env('IP_ADDRESSES', '').split(',')))

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'server@temba.io')
FLOW_FROM_EMAIL = env('FLOW_FROM_EMAIL', "no-reply@temba.io")
EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', 'server@temba.io')
EMAIL_PORT = int(env('EMAIL_PORT', 25))
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', 'mypassword')
EMAIL_USE_TLS = env('EMAIL_USE_TLS', 'on') == 'on'
EMAIL_USE_SSL = env('EMAIL_USE_SSL', 'off') == 'on'

BRANDING["rapidpro.io"].update({
    "logo_link": env('BRANDING_LOGO_LINK', '/'),
    "styles": ['fonts/style.css', ],
    "domain": HOSTNAME,
    "allow_signups": env('BRANDING_ALLOW_SIGNUPS', True),
    "tiers": dict(import_flows=0, multi_user=0, multi_org=0),
    "version": None,
    'has_sso': False,
    'sso_login_url': "",
    'sso_logout_url': "",
})
DEFAULT_BRAND_OBJ = BRANDING["rapidpro.io"]

CHANNEL_TYPES = [
    "temba.channels.types.postmaster.PostmasterType",
    "temba.channels.types.bandwidth_international.BandwidthInternationalType",
    "temba.channels.types.bandwidth.BandwidthType",
    "temba.channels.types.arabiacell.ArabiaCellType",
    "temba.channels.types.whatsapp.WhatsAppType",
    "temba.channels.types.twilio.TwilioType",
    "temba.channels.types.twilio_messaging_service.TwilioMessagingServiceType",
    "temba.channels.types.vonage.VonageType",
    "temba.channels.types.africastalking.AfricasTalkingType",
    "temba.channels.types.blackmyna.BlackmynaType",
    "temba.channels.types.bongolive.BongoLiveType",
    "temba.channels.types.burstsms.BurstSMSType",
    "temba.channels.types.chikka.ChikkaType",
    "temba.channels.types.clickatell.ClickatellType",
    "temba.channels.types.dartmedia.DartMediaType",
    "temba.channels.types.dmark.DMarkType",
    "temba.channels.types.external.ExternalType",
    "temba.channels.types.facebook.FacebookType",
    "temba.channels.types.firebase.FirebaseCloudMessagingType",
    "temba.channels.types.globe.GlobeType",
    "temba.channels.types.highconnection.HighConnectionType",
    "temba.channels.types.hub9.Hub9Type",
    "temba.channels.types.infobip.InfobipType",
    "temba.channels.types.line.LineType",
    "temba.channels.types.m3tech.M3TechType",
    "temba.channels.types.macrokiosk.MacrokioskType",
    "temba.channels.types.mtarget.MtargetType",
    "temba.channels.types.messangi.MessangiType",
    "temba.channels.types.novo.NovoType",
    "temba.channels.types.playmobile.PlayMobileType",
    "temba.channels.types.plivo.PlivoType",
    "temba.channels.types.redrabbit.RedRabbitType",
    "temba.channels.types.shaqodoon.ShaqodoonType",
    "temba.channels.types.smscentral.SMSCentralType",
    "temba.channels.types.start.StartType",
    "temba.channels.types.telegram.TelegramType",
    "temba.channels.types.twiml_api.TwimlAPIType",
    "temba.channels.types.twitter.TwitterType",
    "temba.channels.types.twitter_legacy.TwitterLegacyType",
    "temba.channels.types.verboice.VerboiceType",
    "temba.channels.types.viber_public.ViberPublicType",
    "temba.channels.types.wechat.WeChatType",
    "temba.channels.types.yo.YoType",
    "temba.channels.types.zenvia.ZenviaType",
    "temba.channels.types.android.AndroidType",
]

# how many sequential contacts on import triggers suspension
SEQUENTIAL_CONTACTS_THRESHOLD = env('SEQUENTIAL_CONTACTS_THRESHOLD', 5000)

# Org search filters
ORG_SEARCH_CONTEXT = env('ORG_SEARCH_CONTEXT', '').split(',')

# -----------------------------------------------------------------------------------
# Django-rest-framework configuration
# -----------------------------------------------------------------------------------
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "v2": str(env('API_THROTTLE_RATE', 250000)) + "/hour",
    "v2.contacts": str(env('API_THROTTLE_RATE', 250000)) + "/hour",
    "v2.messages": str(env('API_THROTTLE_RATE', 250000)) + "/hour",
    "v2.broadcasts": str(env('API_THROTTLE_RATE', 250000)) + "/hour",
    "v2.runs": str(env('API_THROTTLE_RATE', 250000)) + "/hour",
    "v2.api": str(env('API_THROTTLE_RATE', 250000)) + "/hour",
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    "root": {"level": "WARNING", "handlers": ["default"]},
    'formatters': {
        'json': {
            '()': 'engage.utils.logs.CustomJsonFormatter',
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'json'
        },
    },
    "loggers": {
        'django': {'handlers': ['default'], 'level': 'INFO', "propagate": False},
        '': {'handlers': ['default'], 'level': 'INFO'},
        "pycountry": {"level": "ERROR", "handlers": ["default"], "propagate": False},
        "django.security.DisallowedHost": {"handlers": ["default"], "propagate": False},
        "django.db.backends": {"level": "ERROR", "handlers": ["default"], "propagate": False},
    },
}
LOGGING['root']['level'] = env('LOG_LEVEL', env('DJANGO_LOG_LEVEL', 'INFO'))

GROUP_PERMISSIONS['Editors'] += (
    "channels.channellog_read",
)

#============== KeyCloak SSO ===================
OAUTH2_CONFIG = OAuthConfig()
if not is_empty(env('KEYCLOAK_URL', None)):
    if OAUTH2_CONFIG.is_enabled:
        DEFAULT_BRAND_OBJ.update({
            'has_sso': not OAUTH2_CONFIG.is_login_replaced,
            'sso_login_url': OAUTH2_CONFIG.get_login_url(),
            # once again, Blacklisted tokens db schema required for OP/total logout
            #'sso_logout_url': OAUTH2_CONFIG.get_logout_url(),
            'sso_logout_url': LOGOUT_URL,
        })
        if OAUTH2_CONFIG.is_login_replaced:
            LOGIN_URL = OAUTH2_CONFIG.get_login_url()
        #endif login is replaced
        if OAUTH2_CONFIG.KEYCLOAK_LOGOUT_REDIRECT:
            LOGOUT_REDIRECT_URL = OAUTH2_CONFIG.KEYCLOAK_LOGOUT_REDIRECT
        #endif logout redirect is defined

        INSTALLED_APPS += (
            'oauth2_authcodeflow',
        )
        AUTHENTICATION_BACKENDS = (
            'oauth2_authcodeflow.auth.AuthenticationBackend',
        ) + AUTHENTICATION_BACKENDS

        # cors middleware not required, yet
        #MIDDLEWARE = MIDDLEWARE[:1] + ('corsheaders.middleware.CorsMiddleware',) + MIDDLEWARE[1:]
        #CORS_ORIGIN_ALLOW_ALL = True #DEBUG-only (replace with actual keycloak URL rather than all

        # plugin settings
        OIDC_OP_DISCOVERY_DOCUMENT_URL = OAUTH2_CONFIG.get_discovery_url()
        OIDC_RP_CLIENT_ID = OAUTH2_CONFIG.KEYCLOAK_CLIENT_ID
        OIDC_RP_CLIENT_SECRET = OAUTH2_CONFIG.KEYCLOAK_CLIENT_SECRET
        OIDC_RP_SCOPES = OAUTH2_CONFIG.SCOPES
        #OIDC_RP_SIGN_ALGOS_ALLOWED = 'RS256' if OAUTH2_CONFIG.OIDC_RSA_PRIVATE_KEY else 'HS256'
        #OIDC_CREATE_USER = False  #docs are wrong as this setting is ignored, a bug, no workaround.
        OIDC_TIMEOUT = 60  # seconds before giving up on OIDC
        # the middleware requires db changes for keeping track of blacklisted tokens, do not use.
        # MIDDLEWARE += (
        #     "oauth2_authcodeflow.middleware.RefreshAccessTokenMiddleware",
        #     "oauth2_authcodeflow.middleware.RefreshSessionMiddleware"
        # )

        # callback to use email as the username, which is a non-standard thing for Django.
        from engage.auth.oauth_utils import oauth_username_is_email
        OIDC_DJANGO_USERNAME_FUNC = oauth_username_is_email

    #endif is_enabled
#endif keycloak

USER_GUIDE_CONFIG = AwsS3Config('USER_GUIDE_')
DEFAULT_BRAND_OBJ.update({
    'has_user_guide': USER_GUIDE_CONFIG.is_defined() or len(USER_GUIDE_CONFIG.FILEPATH) > 1,
})

PM_CONFIG: PMConfig = PMConfig(REDIS_URL, CACHES)

MSG_FIELD_SIZE = env('MSG_FIELD_SIZE', 4096)

# set of ISO-639-3 codes of languages to allow in addition to all ISO-639-1 languages
if env('NON_ISO6391_LANGUAGES_ALLOWED', None) is not None:
    NON_ISO6391_LANGUAGES = tuple(filter(None, env('NON_ISO6391_LANGUAGES_ALLOWED', None).split(',')))
else:
    NON_ISO6391_LANGUAGES = None
# setting the above ^ to None means all are allowed.

#Use CHAT_MODE_CHOICES to configure the chatmodes that are available to the Postmaster channel
from engage.channels.types.postmaster.schemes import PM_Scheme_Default_Chats
CHAT_MODE_CHOICES = PM_Scheme_Default_Chats
