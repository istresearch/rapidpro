from django.apps import AppConfig as BaseAppConfig
from django.conf import settings

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

        # Need this for static file generation, since there is no SSO enabled
        if settings.OAUTH2_CONFIG.is_enabled:
            from .oauth import OAuthOverrides
            OAuthOverrides.applyPatches()

    #enddef ready

#endclass AppConfig
