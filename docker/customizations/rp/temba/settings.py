# -*- coding: utf-8 -*-
from temba.settings_engage import *  # noqa

DEFAULT_BRAND = "rapidpro.io"
BRANDING[DEFAULT_BRAND] = DEFAULT_BRAND_OBJ

# in case an instance defines/overrides any previous setting
try:
    from temba.local_settings import *
except ImportError:
    pass
