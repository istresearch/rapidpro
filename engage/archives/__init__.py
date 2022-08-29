from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.archives.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.archives"
    label = "engage_archives"
    verbose_name = "Engage Archives"