# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from temba.settings_engage import * # noqa


EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = env('EMAIL_HOST_USER', 'server@temba.io')
EMAIL_PORT = int(env('EMAIL_PORT', 25))
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'server@temba.io')
FLOW_FROM_EMAIL = env('FLOW_FROM_EMAIL', "no-reply@temba.io")
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', 'mypassword')
EMAIL_USE_TLS = env('EMAIL_USE_TLS', 'on') == 'on'
EMAIL_USE_SSL = env('EMAIL_USE_SSL', 'off') == 'on'

version_str = None
vtag = env('VERSION_TAG', '')
if vtag:
    version_str = "v{}".format(vtag)

DEFAULT_BRAND = "engage"
DEFAULT_BRAND_OBJ.update({
    'slug': env('BRANDING_SLUG', 'engage'),
    'name': env('BRANDING_NAME', 'Engage'),
    'title': None,
    'org': env('BRANDING_ORG', 'Global Comms'),
    'meta_desc': 'Engage',
    'meta_author': '',
    'colors': dict([rule.split('=') for rule in env('BRANDING_COLORS', 'primary=#0c6596').split(';')]),
    #'styles': DEFAULT_BRAND_OBJ["styles"].extend(['engage.less',]),
    'final_style': 'brands/engage/less/final.less',
    'email': env('BRANDING_EMAIL', 'email@localhost.localdomain'),
    'support_email': env('BRANDING_SUPPORT_EMAIL', 'email@localhost.localdomain'),
    'link': env('BRANDING_LINK', 'https://localhost.localdomain'),
    'api_link': env('BRANDING_API_LINK', 'https://api.localhost.localdomain'),
    'docs_link': env('BRANDING_DOCS_LINK', 'http://docs.localhost.localdomain'),
    'favico': env('BRANDING_FAVICO', 'brands/engage/images/engage.ico'),
    'splash': env('BRANDING_SPLASH', 'brands/engage/images/splash.png'),
    'logo': env('BRANDING_LOGO', 'brands/engage/images/logo.png'),
    'welcome_packs': [dict(size=5000, name="Demo Account"),],
    'description': _("Enabling Global Conversations"),
    'credits': "",
    'version': version_str,
})
BRANDING[DEFAULT_BRAND] = DEFAULT_BRAND_OBJ

# in case an instance defines/overrides any previous setting
try:
    from temba.local_settings import *
except ImportError:
    pass
