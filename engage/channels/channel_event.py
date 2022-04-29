from django.utils.translation import ugettext_lazy as _

from smartmin.views import SmartCRUDL

from engage.msgs.inboxview import BaseInboxView

from temba.channels.models import ChannelEvent
from temba.msgs.models import SystemLabel


class EngageChannelEventCRUDL(SmartCRUDL):
    model = ChannelEvent
    actions = ("calls",)

    class Calls(BaseInboxView):
        title = _("Calls")
        fields = ("contact", "event_type", "channel", "occurred_on")
        default_order = "-occurred_on"
        search_fields = ("contact__urns__path__icontains", "contact__name__icontains")
        system_label = SystemLabel.TYPE_CALLS
        select_related = ("contact", "channel")

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r"^calls/$"

        def get_context_data(self, *args, **kwargs):
            context = super().get_context_data(*args, **kwargs)
            context["actions"] = []
            return context
