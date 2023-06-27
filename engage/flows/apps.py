from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.flows"
    label = "engage_flows"
    verbose_name = "Engage Flows"

    def ready(self):
        from .models import FlowOverrides
        FlowOverrides.setClassOverrides()

        from .views import FlowCRUDLOverrides
        FlowCRUDLOverrides.setClassOverrides()
    #enddef ready

#endclass AppConfig
