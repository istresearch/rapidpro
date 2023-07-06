from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.msgs"
    label = "engage_msgs"
    verbose_name = "Engage Messages"

    def ready(self):
        # override the date picker widget with one we like better
        import smartmin.widgets
        from .datepicker import DatePickerMedia
        smartmin.widgets.DatePickerWidget.Media = DatePickerMedia

        from .models import MsgModelOverride, LabelModelOverride
        MsgModelOverride.setClassOverrides()
        LabelModelOverride.setClassOverrides()

        from .tests import LabelCRUDLTestOverrides
        LabelCRUDLTestOverrides.setClassOverrides()

        from .views.inbox import MsgInboxViewOverrides
        MsgInboxViewOverrides.setClassOverrides()

        # override base inbox class before child classes
        from .inbox_msgfailed import ViewInboxFailedMsgsOverrides
        ViewInboxFailedMsgsOverrides.setClassOverrides()

        from .views.exporter import MsgExporterOverrides
        MsgExporterOverrides.setClassOverrides()

        from temba.msgs.views import MsgCRUDL
        from .views.read import Read
        MsgCRUDL.Read = Read
        MsgCRUDL.actions += ("read",)
    #enddef on_apply_overrides


    #enddef ready

#endclass AppConfig
