from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.triggers"
    label = "engage_triggers"
    verbose_name = "Engage Triggers"

    def ready(self):
        from .views import TriggerCreateOverrides
        TriggerCreateOverrides.applyPatches()
    #enddef ready

#endclass AppConfig
