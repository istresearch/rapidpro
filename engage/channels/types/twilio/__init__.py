from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.channels.types.twilio.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.channels.types.twilio"
    label = "engage_channels_types_twilio"
    verbose_name = "Engage Channels Types Twilio"
