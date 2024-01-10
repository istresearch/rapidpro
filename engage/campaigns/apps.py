from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.campaigns"
    label = "engage_campaigns"
    verbose_name = "Engage Campaigns"

    def ready(self):
        from .views import CampaignCRUDLOverrides
        CampaignCRUDLOverrides.applyPatches()
        from .views import CampaignArchivedOverrides
        CampaignArchivedOverrides.applyPatches()
    #enddef ready

#endclass AppConfig
