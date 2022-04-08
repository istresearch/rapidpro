from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.auth.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.auth"
    label = "engage_auth"
    verbose_name = "Engage Auth"
