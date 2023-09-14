from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.auth"
    label = "engage_auth"
    verbose_name = "Engage Auth"

    def ready(self):
        from .account import AuthUserOverrides
        AuthUserOverrides.applyPatches()

        from .account import TembaUserOverrides
        TembaUserOverrides.applyPatches()
    #enddef ready

#endclass AppConfig
