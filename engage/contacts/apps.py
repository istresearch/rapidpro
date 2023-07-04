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
        ContactFieldOverrides.setClassOverrides()
        from .models import ContactOverrides
        ContactOverrides.setClassOverrides()

        from .views import ContactListOverrides
        ContactListOverrides.setClassOverrides()
        from .views import ContactReadOverrides
        ContactReadOverrides.setClassOverrides()
    #enddef ready

#endclass AppConfig
