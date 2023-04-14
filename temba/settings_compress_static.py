# Django settings when running compress
from getenv import env

from temba.settings import *  # noqa
from temba.settings import (
    STATIC_ROOT,
    STATIC_URL,
    BRANDING,
    DEFAULT_BRAND,
)

COMPRESS_ENABLED = True
COMPRESS_CSS_HASHING_METHOD = "content"

COMPRESS_URL = None
COMPRESS_ROOT = STATIC_ROOT

if env('DEV_STATIC', 'off') != 'on':
    COMPRESS_OFFLINE = True
    COMPRESS_OFFLINE_CONTEXT = dict(
        STATIC_URL=STATIC_URL, base_template="frame.html", brand=BRANDING[DEFAULT_BRAND], debug=False, testing=False
    )
    if env('COMPRESS_WITH_BROTLI', 'off') == 'on':
        COMPRESS_STORAGE = 'compressor.storage.BrotliCompressorFileStorage'
    else:
        COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'
    #endif use Brotli compression
#endif prod
