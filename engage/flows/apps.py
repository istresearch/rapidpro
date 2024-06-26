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

        from .view.create import FlowViewCreate
        FlowViewCreate.applyPatches()

        from .view.update import FlowViewUpdate
        FlowViewUpdate.applyPatches()

        from .view.editor import FlowViewEditor
        FlowViewEditor.applyPatches()

        from .view.simulate import FlowViewSimulate
        FlowViewSimulate.applyPatches()

        from .views import FlowCRUDLOverrides
        FlowCRUDLOverrides.applyPatches()

        from .views import ArchivedViewOverrides
        ArchivedViewOverrides.applyPatches()

        from .views import UploadMediaActionOverrides
        UploadMediaActionOverrides.applyPatches()
    #enddef ready

#endclass AppConfig
