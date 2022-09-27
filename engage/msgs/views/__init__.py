from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.msgs.views.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.msgs.views"
    label = "engage_msgs_views"
    verbose_name = "Engage Message Views"
