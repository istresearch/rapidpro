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
        MsgModelOverride.applyPatches()
        LabelModelOverride.applyPatches()

        from .tests import LabelCRUDLTestOverrides
        LabelCRUDLTestOverrides.applyPatches()

        # override base inbox class before child classes
        from .views.inbox import MsgInboxViewOverrides
        MsgInboxViewOverrides.applyPatches()
        # now we can override "child inbox" classes
        from .views.outbox import ViewMsgsOutboxOverrides
        ViewMsgsOutboxOverrides.applyPatches()
        from .inbox_msgfailed import ViewInboxFailedMsgsOverrides
        ViewInboxFailedMsgsOverrides.applyPatches()

        from .views.exporter import MsgExporterOverrides
        MsgExporterOverrides.applyPatches()

        from temba.msgs.views import MsgCRUDL
        from .views.read import Read
        MsgCRUDL.Read = Read
        MsgCRUDL.actions += ("read",)
    #enddef ready

#endclass AppConfig
