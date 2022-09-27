from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.orgs.views.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.orgs.views"
    label = "engage_orgs_views"
    verbose_name = "Engage Orgs Views"
#endclass AppConfig
