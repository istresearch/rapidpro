from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage"
    label = "engage"
    verbose_name = "Engage"
