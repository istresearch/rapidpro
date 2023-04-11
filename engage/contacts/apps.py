from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.contacts"
    label = "engage_contacts"
    verbose_name = "Engage Contacts"
