from django.apps import AppConfig as BaseAppConfig

# NOTE: AppConfig moved into apps.py converting from Django v2 to v4, reason:
#       The v3 deprecated `default_app_config` var was removed in v3.10
#       https://code.djangoproject.com/ticket/31180
# apps.py is the "default" method for defining AppConfigs in v4:
# https://docs.djangoproject.com/en/4.0/ref/applications/#configuring-applications

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.utils"
    label = "engage_utils"
    verbose_name = "Engage Utilities"

    def ready(self):
        from .views import BaseListViewOverrides
        BaseListViewOverrides.setClassOverrides()

        from .views import MultipleObjectMixinOverrides
        MultipleObjectMixinOverrides.setClassOverrides()

        from temba.utils import models as TUM
        from .models import RequireUpdateFieldsMixin
        TUM.RequireUpdateFieldsMixin = RequireUpdateFieldsMixin

        from .views import BulkActionMixinOverrides
        BulkActionMixinOverrides.setClassOverrides()

        from .export import BaseExportTaskOverrides
        BaseExportTaskOverrides.setClassOverrides()
    #enddef ready

#endclass AppConfig
