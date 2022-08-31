from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.utils.templatetags.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.utils.templatetags"
    label = "engage_utils_templatetags"
    verbose_name = "Engage Template Tags"
