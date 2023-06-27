from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.mailroom"
    label = "engage_mailroom"
    verbose_name = "Engage Mailroom"

    def ready(self):
        from temba.mailroom.events import event_renderers
        from .events import getHistoryContentFromMsg, getHistoryContentFromChannelEvent
        from temba.msgs.models import Msg, ChannelEvent
        event_renderers[Msg] = getHistoryContentFromMsg
        event_renderers[ChannelEvent] = getHistoryContentFromChannelEvent
    #enddef ready

#endclass AppConfig
