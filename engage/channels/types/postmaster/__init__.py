from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.channels.types.postmaster.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.channels.types.postmaster"
    label = "engage_channels_types_postmaster"
    verbose_name = "Engage Channels Types Postmaster"
