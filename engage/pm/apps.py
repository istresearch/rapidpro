from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.pm"
    label = "engage_pm"
    verbose_name = "Engage PM"

    def ready(self):
        pass
    #enddef ready

#endclass AppConfig
