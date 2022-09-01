from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.contacts.templatetags.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.contacts.templatetags"
    label = "engage_contacts_templatetags"
    verbose_name = "Engage Contacts Template Tags"
