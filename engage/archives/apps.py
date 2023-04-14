from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.archives"
    label = "engage_archives"
    verbose_name = "Engage Archives"

    def ready(self):
        from .models import ArchiveOverrides
        ArchiveOverrides.setClassOverrides()
    #enddef ready

#endclass AppConfig
