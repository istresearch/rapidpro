from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.contacts"
    label = "engage_contacts"
    verbose_name = "Engage Contacts"

    def ready(self):
        from .models import ContactFieldOverrides
        ContactFieldOverrides.applyPatches()
        from .models import ContactOverrides
        ContactOverrides.applyPatches()

        from .views import ContactListOverrides
        ContactListOverrides.applyPatches()
        from .views import ContactReadOverrides
        ContactReadOverrides.applyPatches()
        from .views import ContactHistoryOverrides
        ContactHistoryOverrides.applyPatches()
    #enddef ready

#endclass AppConfig
