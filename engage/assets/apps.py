from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.assets"
    label = "engage_assets"
    verbose_name = "Engage Assets"

    def ready(self):
        from .models import BaseAssetStorePatcher
        BaseAssetStorePatcher.applyPatches()
    #enddef ready

#endclass AppConfig
