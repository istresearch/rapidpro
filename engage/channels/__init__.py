from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.channels.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.channels"
    label = "engage_channels"
    verbose_name = "Engage Channels"
