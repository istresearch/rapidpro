# Django settings when running compress
from getenv import env
import os

from temba.settings import *  # noqa


COMPRESS_ENABLED = True
COMPRESS_CSS_HASHING_METHOD = "content"

COMPRESS_URL = None
COMPRESS_ROOT = STATIC_ROOT

COMPRESS_PRECOMPILERS = (
    ("text/less", 'lessc --include-path="%s:%s" {infile} {outfile}' % (
        os.path.join(COMPRESS_ROOT, "less"),
        os.path.join(COMPRESS_ROOT, "engage", "less"),
    )),
)

if env('DEV_STATIC', 'off') != 'on':
    COMPRESS_OFFLINE = True
    COMPRESS_OFFLINE_CONTEXT = dict(
        STATIC_URL=STATIC_URL, base_template="frame.html", brand=BRANDING[DEFAULT_BRAND], debug=False, testing=False
    )
    COMPRESS_STORAGE = 'compressor.storage.GzipCompressorFileStorage'
