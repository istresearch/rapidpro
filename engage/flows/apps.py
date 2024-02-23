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
        FlowOverrides.applyPatches()

        from .view.create import CreateFlowOverrides
        CreateFlowOverrides.applyPatches()

        from .views import FlowCRUDLOverrides
        FlowCRUDLOverrides.applyPatches()

        from .views import ArchivedViewOverrides
        ArchivedViewOverrides.applyPatches()

        from .views import UploadMediaActionOverrides
        UploadMediaActionOverrides.applyPatches()
    #enddef ready

#endclass AppConfig
