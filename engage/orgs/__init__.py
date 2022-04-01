from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.orgs.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.orgs"
    label = "engage_orgs"
    verbose_name = "Engage Orgs"