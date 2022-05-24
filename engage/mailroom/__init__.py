from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.mailroom.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.mailroom"
    label = "engage_mailroom"
    verbose_name = "Engage Mailroom"
