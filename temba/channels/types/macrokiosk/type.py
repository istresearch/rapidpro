from django.utils.translation import gettext_lazy as _

from temba.channels.types.macrokiosk.views import ClaimView
from temba.contacts.models import URN

from ...models import ChannelType


class MacrokioskType(ChannelType):
    """
    An Macrokiok channel (http://www.macrokiosk.com/)
    """

    code = "MK"
    category = ChannelType.Category.PHONE

    courier_url = r"^mk/(?P<uuid>[a-z0-9\-]+)/(?P<action>status|receive)$"

    name = "Macrokiosk"

    claim_blurb = _("Easily add a two way number you have configured with %(link)s using their APIs.") % {
        "link": '<a href="http://macrokiosk.com/">Macrokiosk</a>'
    }
    claim_view = ClaimView

    schemes = [URN.TEL_SCHEME]
    max_length = 1600

    attachment_support = False

    configuration_blurb = _(
        "To finish configuring your MACROKIOSK connection you'll need to notify MACROKIOSK of the following URLs."
    )

    configuration_urls = (
        dict(
            label=_("Inbound URL"),
            url="https://{{ channel.callback_domain }}{% url 'courier.mk' channel.uuid 'receive' %}",
            description=_(
                "This endpoint should be called by MACROKIOSK when new messages are received to your number."
            ),
        ),
        dict(
            label=_("DLR URL"),
            url="https://{{ channel.callback_domain }}{% url 'courier.mk' channel.uuid 'status' %}",
            description=_(
                "This endpoint should be called by MACROKIOSK when the message status changes. (delivery reports)"
            ),
        ),
    )

    available_timezones = ["Asia/Kuala_Lumpur"]
