from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.msgs.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.msgs"
    label = "engage_msgs"
    verbose_name = "Engage Messages"
