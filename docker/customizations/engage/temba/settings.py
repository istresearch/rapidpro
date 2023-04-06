# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from getenv import env
from datetime import datetime
from django.utils.translation import gettext_lazy as _

from temba.settings_engage import *  # noqa

version_str = None
vtag = env('VERSION_TAG', '')
vstr = env('VERSION_CI', '')
if vtag and vstr and vtag.startswith('ci'):
    version_str = f"{vstr} ({vtag})"
elif vtag and vtag.startswith('ci'):
    version_str = f"{vtag}"
elif vtag:
    version_str = f"v{vtag}"

DEFAULT_BRAND = "engage"
DEFAULT_BRAND_OBJ.update({
    'slug': env('BRANDING_SLUG', 'pulse'),
    'name': env('BRANDING_NAME', 'Pulse'),
    'title': env('BRANDING_TITLE', 'Engage'),
    'org': env('BRANDING_ORG', 'TST'),
    'meta_desc': 'Pulse Engage',
    'meta_author': 'Two Six Technologies',
    'colors': dict([rule.split('=') for rule in env('BRANDING_COLORS', 'primary=#0c6596').split(';')]),
    'styles': DEFAULT_BRAND_OBJ["styles"].extend(['brands/engage/font/style.css', ]),
    'final_style': 'brands/engage/less/final.less',
    'email': env('BRANDING_EMAIL', 'pulse@istresearch.com'),
    'support_email': env('BRANDING_SUPPORT_EMAIL', 'pulse@istresearch.com'),
    'link': env('BRANDING_LINK', 'https://twosixtech.com'),
    'api_link': env('BRANDING_API_LINK', ''),
    'docs_link': env('BRANDING_DOCS_LINK', ''), #deprecated, not used anywhere
    'favico': env('BRANDING_FAVICO', 'brands/engage/images/engage.ico'),
    'splash': env('BRANDING_SPLASH', 'brands/engage/images/splash.png'),
    'logo': env('BRANDING_LOGO', 'brands/engage/images/logo.svg'),
    'description': _("Addressing the most urgent human security issues faced by the world’s vulnerable populations."),
    'credits': _("&copy; 2012-%s Two Six Technologies, and others. All Rights Reserved." % (
        datetime.now().strftime('%Y')
    )),
    'version': version_str,
})
BRANDING[DEFAULT_BRAND] = DEFAULT_BRAND_OBJ

# in case an instance defines/overrides any previous setting
try:
    from temba.local_settings import *
except ImportError:
    pass
