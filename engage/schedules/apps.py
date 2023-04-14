from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.schedules"
    label = "engage_schedules"
    verbose_name = "Engage Schedules"

    def ready(self):
        from .tests import ScheduleTestOverrides
        ScheduleTestOverrides.setClassOverrides()
    #enddef ready

#endclass AppConfig
