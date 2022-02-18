# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# -----------------------------------------------------------------------------------
# RapidPro settings file for the docker setup
# -----------------------------------------------------------------------------------

from getenv import env
import dj_database_url
import django_cache_url
from datetime import datetime
from django.utils.translation import ugettext_lazy as _
from temba.settings_common import *  # noqa

SUB_DIR = env('SUB_DIR', required=False)
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
    tuple(filter(lambda tup : tup not in env('REMOVE_INSTALLED_APPS', '').split(','), INSTALLED_APPS)) +
    tuple(filter(None, env('EXTRA_INSTALLED_APPS', '').split(','))))

ROOT_URLCONF = env('ROOT_URLCONF', 'temba.urls')

DEBUG = env('DJANGO_DEBUG', 'off') == 'on'

GEOS_LIBRARY_PATH = '/usr/local/lib/libgeos_c.so'
GDAL_LIBRARY_PATH = '/usr/local/lib/libgdal.so'

SECRET_KEY = env('SECRET_KEY', required=True)
DATABASE_URL = env('DATABASE_URL', required=True)
DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}
DATABASES['default']['CONN_MAX_AGE'] = 60
DATABASES['default']['ATOMIC_REQUESTS'] = True
DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
REDIS_URL = env('REDIS_URL', required=True)
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
#if TEMBA_HOST.lower().startswith('https://') or IS_PROD:
#    from .security_settings import *  # noqa
SECURE_PROXY_SSL_HEADER = (env('SECURE_PROXY_SSL_HEADER', 'HTTP_X_FORWARDED_PROTO'), 'https')
INTERNAL_IPS = ('*',)
ALLOWED_HOSTS = env('ALLOWED_HOSTS', HOSTNAME).split(';')

LOGGING['root']['level'] = env('DJANGO_LOG_LEVEL', 'INFO')

AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', '')
AWS_S3_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', '')
AWS_S3_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', '')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', 'us-east-1')
IS_AWS_S3_REGION_DEFAULT = bool(AWS_S3_REGION_NAME == 'us-east-1')
AWS_SIGNED_URL_DURATION = int(env('AWS_SIGNED_URL_DURATION', '1800'))
AWS_DEFAULT_ACL = env('AWS_DEFAULT_ACL', '')
AWS_LOCATION = env('AWS_LOCATION', '')
AWS_QUERYSTRING_EXPIRE = '157784630' #unsure why this is hardcoded as a string
AWS_STATIC = env('AWS_STATIC', bool(AWS_STORAGE_BUCKET_NAME))
AWS_MEDIA = env('AWS_MEDIA', bool(AWS_STORAGE_BUCKET_NAME))
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
    if SUB_DIR is not None and len(SUB_DIR) > 0:
        MEDIA_URL = f"{SUB_DIR}{MEDIA_URL}"
    STORAGE_URL = MEDIA_URL[:-1]

if not AWS_STATIC:
    if SUB_DIR is not None and len(SUB_DIR) > 0:
        STATIC_URL = '/' + SUB_DIR + '/sitestatic/'

    # @see whitenoise middleware usage: https://whitenoise.evans.io/en/stable/django.html
    STATICFILES_STORAGE = 'temba.storage.WhiteNoiseStaticFilesStorage'
    # insert just after security middleware (which is at idx 0)
    MIDDLEWARE = MIDDLEWARE[:1] + ('whitenoise.middleware.WhiteNoiseMiddleware',) + MIDDLEWARE[1:]
    WHITENOISE_MANIFEST_STRICT = False

COMPRESS_ENABLED = env('DJANGO_COMPRESSOR', 'on') == 'on'
COMPRESS_OFFLINE = False

COMPRESS_URL = STATIC_URL
# Use MEDIA_ROOT rather than STATIC_ROOT because it already exists and is
# writable on the server. It's also the directory where other cached files
# (e.g., translations) are stored
COMPRESS_ROOT = STATIC_ROOT
COMPRESS_CSS_HASHING_METHOD = 'content'
COMPRESS_OFFLINE_MANIFEST = 'manifest-%s.json' % env('RAPIDPRO_VERSION', required=True)

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

version_str = None
vtag = env('VERSION_TAG', '')
vstr = env('VERSION_CI', '')
if vtag and vstr and vtag.startswith('ci'):
    version_str = "v{} ({})".format(vstr, vtag)
elif vtag:
    version_str = "v{}".format(vtag)

try:
    BRANDING
except NameError:
    BRANDING = {}

BRANDING['engage'] = {
    'logo_link': env('BRANDING_LOGO_LINK', '/{}/'.format(SUB_DIR) if SUB_DIR is not None else '/'),
    'slug': env('BRANDING_SLUG', 'pulse'),
    'name': env('BRANDING_NAME', 'Pulse'),
    'title': env('BRANDING_TITLE', 'Engage'),
    'org': env('BRANDING_ORG', 'IST'),
    'meta_desc': 'Pulse Engage',
    'meta_author': 'IST Research Corp',
    'colors': dict([rule.split('=') for rule in env('BRANDING_COLORS', 'primary=#0c6596').split(';')]),
    'styles': ['brands/engage/font/style.css', 'brands/engage/less/style.less', 'fonts/style.css'],
    'final_style': 'brands/engage/less/engage.less',
    'welcome_topup': 1000,
    'email': env('BRANDING_EMAIL', 'pulse@istresearch.com'),
    'support_email': env('BRANDING_SUPPORT_EMAIL', 'pulse@istresearch.com'),
    'link': env('BRANDING_LINK', 'https://istresearch.com'),
    'api_link': env('BRANDING_API_LINK', 'https://api.rapidpro.io'),
    'docs_link': env('BRANDING_DOCS_LINK', 'http://docs.rapidpro.io'),
    'domain': HOSTNAME,
    'favico': env('BRANDING_FAVICO', 'brands/engage/images/engage.ico'),
    'splash': env('BRANDING_SPLASH', 'brands/engage/images/splash.png'),
    'logo': env('BRANDING_LOGO', 'brands/engage/images/logo.svg'),
    'allow_signups': env('BRANDING_ALLOW_SIGNUPS', True),
    "flow_types": ["M", "V", "S"],  # see Flow.TYPE_MESSAGE, Flow.TYPE_VOICE, Flow.TYPE_SURVEY
    'tiers': dict(import_flows=0, multi_user=0, multi_org=0),
    'bundles': [],
    'welcome_packs': [dict(size=5000, name="Demo Account"), dict(size=100000, name="UNICEF Account")],
    'description': _("Addressing the most urgent human security issues faced by the world’s vulnerable populations."),
    'credits': _("Copyright &copy; 2012-%s IST Research Corp, and others. All Rights Reserved." % (
        datetime.now().strftime('%Y')
    )),
    'version': version_str
}

DEFAULT_BRAND = 'engage'

if 'SUB_DIR' in locals() and SUB_DIR is not None:
    BRANDING[DEFAULT_BRAND]["sub_dir"] = SUB_DIR
    LOGIN_URL = "/" + SUB_DIR + "/users/login/"
    LOGOUT_URL = "/" + SUB_DIR + "/users/logout/"
    LOGIN_REDIRECT_URL = "/" + SUB_DIR + "/org/choose/"
    LOGOUT_REDIRECT_URL = "/" + SUB_DIR + "/"

# build up our offline compression context based on available brands
COMPRESS_OFFLINE_CONTEXT = []
for brand in BRANDING.values():
    context = dict(STATIC_URL=STATIC_URL, base_template='frame.html', debug=False, testing=False)
    context['brand'] = dict(slug=brand['slug'], styles=brand['styles'])
    COMPRESS_OFFLINE_CONTEXT.append(context)

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
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(created)f %(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'json'
        },
    },
    "loggers": {
        'django': {'handlers': ['default'],'level': 'INFO'},
        '': {'handlers': ['default'], 'level': 'INFO'},
        "pycountry": {"level": "ERROR", "handlers": ["default"], "propagate": False},
        "django.security.DisallowedHost": {"handlers": ["default"], "propagate": False},
        "django.db.backends": {"level": "ERROR", "handlers": ["default"], "propagate": False},
    },
}

ORG_SEARCH_CONTEXT = []

MSG_FIELD_SIZE = env('MSG_FIELD_SIZE', 4096)

# unset BWI key, causes exception if set and we no longer support it anyway
BWI_KEY = None
# above didn't seem to work, so set ENV var to "" for now, debug later.

# set of ISO-639-3 codes of languages to allow in addition to all ISO-639-1 languages
if env('NON_ISO6391_LANGUAGES_ALLOWED', None) is not None:
    NON_ISO6391_LANGUAGES = tuple(filter(None, env('NON_ISO6391_LANGUAGES_ALLOWED', None).split(',')))
else:
    NON_ISO6391_LANGUAGES = None
# setting the above ^ to None means all are allowed.
