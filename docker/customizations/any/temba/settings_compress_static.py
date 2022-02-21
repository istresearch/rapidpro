# Django settings when running compress
from temba.settings import *  # noqa


COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
COMPRESS_CSS_HASHING_METHOD = "content"

COMPRESS_URL = STATIC_URL
COMPRESS_ROOT = STATIC_ROOT
#COMPRESS_STORAGE = 'django.core.files.storage.FileSystemStorage'

COMPRESS_OFFLINE_CONTEXT = dict(
    STATIC_URL=STATIC_URL, base_template="frame.html", brand=BRANDING[DEFAULT_BRAND], debug=False, testing=False
)
