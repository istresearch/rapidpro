# -*- coding: utf-8 -*-
from copy import deepcopy

# -----------------------------------------------------------------------------------
# Engage settings file
# -----------------------------------------------------------------------------------

from getenv import env  # django-getenv package
from glob import glob
import dj_database_url
import django_cache_url  # django-cache-url package

from engage.auth.oauth_config import OAuthConfig
from engage.utils.strings import is_empty, str2bool
from engage.utils.pm_config import PMConfig
from engage.utils.s3_config import AwsS3Config

from temba.settings_common import *  # noqa

SUB_DIR = env('SUB_DIR', required=False)
# NOTE: we do not support SUB_DIR anymore, kits no longer use it. Feel free to rip out.
if not is_empty(SUB_DIR):
    MIDDLEWARE += ("engage.utils.middleware.SubdirMiddleware",)
#endif

COURIER_URL = env('COURIER_URL', 'http://localhost:8080')
DEFAULT_TPS = env('DEFAULT_TPS', 10)    # Default Transactions Per Second for newly create Channels.
MAX_TPS = env('MAX_TPS', 50)            # Max configurable Transactions Per Second for newly Created Channels and Updated Channels.

ORG_LIMIT_DEFAULTS["channels"] = sys.maxsize
ORG_LIMIT_DEFAULTS["labels"] = int(env('MAX_ORG_LABELS', 500))

POST_OFFICE_API_URL = env('POST_OFFICE_API_URL', 'http://postoffice:8088/postoffice')
POST_OFFICE_QR_URL = env('POST_OFFICE_QR_URL', f"{POST_OFFICE_API_URL}/engage/claim")
POST_OFFICE_API_KEY = env('POST_OFFICE_API_KEY', 'abc123')

POST_MASTER_DL_URL = env('POST_MASTER_DL_URL', required=False)
POST_MASTER_DL_QRCODE = env('POST_MASTER_DL_QRCODE', required=False)
if POST_MASTER_DL_QRCODE is not None and not POST_MASTER_DL_QRCODE.startswith("data:"):
    POST_MASTER_DL_QRCODE = "data:png;base64, {}".format(POST_MASTER_DL_QRCODE)

MAILROOM_URL=env('MAILROOM_URL', 'http://localhost:8000')

INSTALLED_APPS = (
    tuple(filter(lambda tup: tup not in env('REMOVE_INSTALLED_APPS', '').split(','), INSTALLED_APPS)) + (
        'flatpickr',
        'temba.ext',
        'engage.api',
        'engage.assets',
        'engage.auth',
        'engage.channels',
        'engage.contacts',
        'engage.flows',
        'engage.mailroom',
        'engage.msgs',
        'engage.orgs',
        'engage.schedules',
        'engage.utils',
    ) + tuple(filter(None, env('EXTRA_INSTALLED_APPS', '').split(',')))
)

APP_URLS += (
    'temba.ext.urls',
    'engage.api.urls',
    'engage.auth.urls',
    'engage.utils.user_guide',
)
HANDLER_403 = 'engage.utils.views.permission_denied'
HANDLER_404 = 'engage.utils.views.page_not_found'
HANDLER_500 = 'engage.utils.views.server_error'

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
# slightly updated on move to debian-base-image, should work on either as it s now.
try:
    GDAL_LIBRARY_PATH = glob('/usr/lib/libgdal.so*')[0]
    GEOS_LIBRARY_PATH = glob('/usr/lib/libgeos_c.so*')[0]
except:
    GEOS_LIBRARY_PATH = '/usr/local/lib/libgeos_c.so'
    GDAL_LIBRARY_PATH = '/usr/local/lib/libgdal.so'
#endtry locate GDAL library executable

SECRET_KEY = env('SECRET_KEY', required=True)

DATABASE_URL = env('DATABASE_URL', required=True)
_db_rw_config = dj_database_url.parse(
    url=DATABASE_URL,
    engine="django.contrib.gis.db.backends.postgis",
    conn_max_age=env('DATABASE_CONN_MAX_AGE', 60),
)
_db_rw_config["ATOMIC_REQUESTS"] = True
_db_rw_config["DISABLE_SERVER_SIDE_CURSORS"] = True
_db_ro_config = deepcopy(_db_rw_config)
#print(_db_rw_config)
DATABASES = {"default": _db_rw_config, "readonly": _db_ro_config}

REDIS_URL = env('REDIS_URL')
if REDIS_URL:
    CELERY_BROKER_URL = env('BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', REDIS_URL)
    CACHE_URL = env('CACHE_URL', REDIS_URL)
    if CACHES['default']['BACKEND'] == 'django_redis.cache.RedisCache':
        CACHES['default']['LOCATION'] = REDIS_URL
        if 'OPTIONS' not in CACHES['default']:
            CACHES['default']['OPTIONS'] = {}
        #endif
        CACHES['default']['OPTIONS']['CLIENT_CLASS'] = 'django_redis.client.DefaultClient'
    #endif default cache definition is what we expect
#endif Redis defined

IS_PROD = env('IS_PROD', 'off') == 'on'
# -----------------------------------------------------------------------------------
# Used when creating callbacks for Twilio, Nexmo etc..
# -----------------------------------------------------------------------------------
HOSTNAME = env('DOMAIN_NAME', 'localhost')
HOST_SCHEME = env('DOMAIN_SCHEME', "https" if HOSTNAME != "localhost" else "http")
HOST_ORIGIN = HOST_SCHEME + "://" + HOSTNAME

STATIC_HOST = env('STATIC_HOST', "") if not DEBUG else ""
STATIC_URL = STATIC_HOST + "/sitestatic/"

if HOST_SCHEME.lower() == 'https' and str2bool(env('USE_SECURE_COOKIES', False)):
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
if env('CSRF_TRUSTED_ORIGINS', None) is not None:
    CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS', None).split(',')
#endif

AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', '')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', '')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', 'us-east-1')
IS_AWS_S3_REGION_DEFAULT = bool(AWS_S3_REGION_NAME == 'us-east-1')
AWS_SIGNED_URL_DURATION = int(env('AWS_SIGNED_URL_DURATION', '1800'))
AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL', None)
AWS_LOCATION = env('AWS_LOCATION', '')
# AWS now saying that it must be less than a week, i.e. < 604800
AWS_QUERYSTRING_EXPIRE = env('AWS_QUERYSTRING_EXPIRE', 604800-1)
AWS_STATIC = bool(AWS_STORAGE_BUCKET_NAME) and env('AWS_STATIC', False)
AWS_MEDIA = bool(AWS_STORAGE_BUCKET_NAME) and env('AWS_MEDIA', True)
AWS_S3_USE_SSL = bool(env('AWS_S3_USE_SSL', True))
AWS_S3_HTTP_SCHEME = "https" if AWS_S3_USE_SSL else "http"
AWS_S3_VERIFY = env('AWS_S3_VERIFY', None)
AWS_S3_CUSTOM_DOMAIN_NAME = env('AWS_S3_CUSTOM_DOMAIN_NAME', None)
AWS_S3_URL = env('AWS_S3_CUSTOM_URL', None)
AWS_S3_ENDPOINT_URL = env('AWS_S3_ENDPOINT_URL', AWS_S3_URL)
#TODO someday, clean all this up: https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
#TODO also expand/re-use our utils/s3_config class
AWS_S3_ADDRESSING_STYLE = env('AWS_S3_ADDRESSING_STYLE', None)  # 'virtual' or 'path'
# As of boto3 version 1.13.21 the default signature version used for generating pre-signed
# urls is still the legacy s3 (also known as v2) version. To be able to access your
# s3 objects in all regions through pre-signed urls, explicitly set this to s3v4.
AWS_S3_SIGNATURE_VERSION = env('AWS_S3_SIGNATURE_VERSION', 's3v4')

if AWS_STORAGE_BUCKET_NAME:
    if AWS_S3_URL is None:
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
            thePathPrefix = env('AWS_S3_PATH_PREFIX', '')  # MUST START WITH A SLASH, eg. '/s3'
            AWS_S3_DOMAIN = f"{theDefaultRegionDomainSegment}s3{theRegionDomainSegment}.{theBaseDomain}{thePathPrefix}"
        #endif custom domain name

        # middleware still expects us-east-1 in special domain format with bucket leading the subdomain (legacy format).
        theBucketPathSegment = f"/{AWS_STORAGE_BUCKET_NAME}" if not IS_AWS_S3_REGION_DEFAULT else ''
        AWS_S3_URL = f"{AWS_S3_HTTP_SCHEME}://{AWS_S3_DOMAIN}{theBucketPathSegment}"
    #endif need to construct AWS_S3_URL

    if AWS_S3_URL.endswith('/'):
        AWS_S3_URL = AWS_S3_URL[:-1]
    #endif remove any trailing slash

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
    #endif aws static in use

    if AWS_MEDIA:
        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        STORAGE_URL = env('STORAGE_URL', AWS_S3_URL)
        if STORAGE_URL.endswith('/'):
            STORAGE_URL = STORAGE_URL[:-1]
        #endif remove any trailing slash
        MEDIA_URL = env('MEDIA_URL', f"{STORAGE_URL}/media/")
        if not MEDIA_URL.endswith('/'):
            MEDIA_URL = MEDIA_URL+'/'
        #endif ensure trailing slash
    #endif aws media in use
#endif aws s3 bucket name defined

if not AWS_MEDIA:
    MEDIA_URL = env('MEDIA_URL', '/media/')
    if not MEDIA_URL.endswith('/'):
        MEDIA_URL = MEDIA_URL+'/'
    #endif ensure trailing slash
    STORAGE_URL = env('STORAGE_URL', MEDIA_URL[:-1])
    if STORAGE_URL.endswith('/'):
        STORAGE_URL = STORAGE_URL[:-1]
    #endif remove any trailing slash
#endif not using aws s3 for media

if not AWS_STATIC:
    # @see whitenoise middleware usage: https://whitenoise.evans.io/en/stable/django.html
    STATICFILES_STORAGE = 'engage.utils.storage.EngageStaticFilesStorage'
    # insert just after security middleware (which is at idx 0)
    MIDDLEWARE = MIDDLEWARE[:1] + ('whitenoise.middleware.WhiteNoiseMiddleware',) + MIDDLEWARE[1:]
    WHITENOISE_MANIFEST_STRICT = False
    #WHITENOISE_KEEP_ONLY_HASHED_FILES = True  # cannot keep only hashed unless we purge {STATIC_URL} from .haml files.
    DEBUG_PROPAGATE_EXCEPTIONS = True
#endif not using aws s3 for staticfiles

STATIC_ROOT = os.path.join(PROJECT_DIR, "../sitestatic/")

COMPRESS_ENABLED = env('DJANGO_COMPRESSOR', 'on') == 'on'
# If COMPRESS_OFFLINE is False, compressor will look in COMPRESS_STORAGE for
# previously processed results, but if not found, will create them on the fly
# and save them to use again.
#COMPRESS_OFFLINE = False
COMPRESS_OFFLINE = COMPRESS_ENABLED and (env('DEV_STATIC', 'off') != 'on')
if COMPRESS_OFFLINE:
    COMPRESS_OFFLINE_MANIFEST = f"manifest-webapp.json"
#endif
if COMPRESS_ENABLED:
    COMPRESS_URL = STATIC_URL
    COMPRESS_ROOT = STATIC_ROOT
    #COMPRESS_STORAGE = STATICFILES_STORAGE

    # compress_precompilers used for static LESS files whether or not COMPRESS_ENABLED==True
    COMPRESS_PRECOMPILERS = (
        ("text/less", 'lessc --include-path="%s:%s" {infile} {outfile}' % (
            os.path.join(COMPRESS_ROOT, "less"),
            os.path.join(COMPRESS_ROOT, "engage", "less"),
        )),
    )
#endif compress on

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

ORG_PLAN_TOPUP = TOPUP_PLAN
ORG_PLAN_ENGAGE = 'managed'
# Default plan for new orgs
DEFAULT_PLAN = ORG_PLAN_ENGAGE
# default keys for all brands
BRANDING["rapidpro.io"].update({
    "logo_link": env('BRANDING_LOGO_LINK', '/'),
    "styles": ['fonts/style.css', ],
    "domain": HOSTNAME,
    "allow_signups": env('BRANDING_ALLOW_SIGNUPS', True),
    "tiers": dict(import_flows=0, multi_user=0, multi_org=0),
    "version": None,
    "default_plan": ORG_PLAN_ENGAGE,
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

PERMISSIONS['*'] += (
    "read_list",  # can read an object, viewing its details
)
PERMISSIONS['orgs.org'] += (
    "assign_user",
    "transfer_to_account",
    "bandwidth_account",
    "bandwidth_connect",
    "postmaster_connect",
    "postmaster_account",
)
PERMISSIONS['msgs.msg'] += (
    "test",
)

# any changes to group permissions requires container script ./db-update.sh be run.
GROUP_PERMISSIONS['Administrators'] += (
    "apks.apk_create",
    "apks.apk_list",
    "apks.apk_update",
    "orgs.org_transfer_to_account",
    "orgs.org_bandwidth_account",
    "orgs.org_bandwidth_connect",
    "orgs.org_postmaster_account",
    "orgs.org_postmaster_connect",
)
GROUP_PERMISSIONS['Editors'] += (
    "channels.channellog_read",
)

# remove "delete channel" from the Editors Role
GROUP_PERMISSIONS['Editors'] = tuple(
    item for item in GROUP_PERMISSIONS['Editors'] if item != "channels.channel_delete"
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

        OIDC_UNUSABLE_PASSWORD = OAUTH2_CONFIG.OIDC_UNUSABLE_PASSWORD

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
PAGINATE_CHANNELS_COUNT = int(env("PAGINATE_CHANNELS_COUNT", 25))
# -----------------------------------------------------------------------------------
# Installs can also choose how long to keep SyncEvents around. Default is 7 days.
# -----------------------------------------------------------------------------------
SYNC_EVENT_TRIM_DAYS = 7

# set of ISO-639-3 codes of languages to allow in addition to all ISO-639-1 languages
if env('NON_ISO6391_LANGUAGES_ALLOWED', None) is not None:
    NON_ISO6391_LANGUAGES = tuple(filter(None, env('NON_ISO6391_LANGUAGES_ALLOWED', None).split(',')))
else:
    NON_ISO6391_LANGUAGES = None
# setting the above ^ to None means all are allowed.

#Use CHAT_MODE_CHOICES to configure the chatmodes that are available to the Postmaster channel
from engage.channels.types.postmaster.schemes import PM_Scheme_Default_Chats
CHAT_MODE_CHOICES = PM_Scheme_Default_Chats

mwl = list(MIDDLEWARE)
# replace BrandingMiddleware
idx = mwl.index("temba.middleware.BrandingMiddleware")
mwl[idx] = "engage.utils.middleware.BrandingMiddleware"
# add custom middleware
mwl.append("engage.utils.middleware.RedirectMiddleware")
MIDDLEWARE = tuple(mwl)

ALT_CALLBACK_DOMAIN = env('ALT_CALLBACK_DOMAIN', None)

ASYNC_MESSAGE_EXPORT = env('ASYNC_MESSAGE_EXPORT', 'on') == 'on'

EXPORT_TASK_CHECK_HOURS = env('EXPORT_TASK_CHECK_HOURS', 4)
