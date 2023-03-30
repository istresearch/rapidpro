from django.utils.translation import gettext_lazy as _

from temba.channels.views import AuthenticatedExternalClaimView
from temba.contacts.models import URN

from ...models import ChannelType


class M3TechType(ChannelType):
    """
    An M3 Tech channel (http://m3techservice.com)
    """

    code = "M3"
    category = ChannelType.Category.PHONE

    courier_url = r"^m3/(?P<uuid>[a-z0-9\-]+)/(?P<action>sent|delivered|failed|received|receive)$"

    name = "M3 Tech"

    claim_blurb = _("Easily add a two way number you have configured with %(link)s using their APIs.") % {
        "link": '<a href="http://m3techservice.com">M3 Tech</a>'
    }
    claim_view = AuthenticatedExternalClaimView

    schemes = [URN.TEL_SCHEME]
    max_length = 160
    attachment_support = False

    configuration_blurb = _(
        "To finish configuring your connection you'll need to notify M3Tech of the following callback URLs."
    )

    configuration_urls = (
        dict(
            label=_("Received URL"),
            url="https://{{ channel.callback_domain }}{% url 'courier.m3' channel.uuid 'receive' %}",
        ),
        dict(
            label=_("Sent URL"), url="https://{{ channel.callback_domain }}{% url 'courier.m3' channel.uuid 'sent' %}"
        ),
        dict(
            label=_("Delivered URL"),
            url="https://{{ channel.callback_domain }}{% url 'courier.m3' channel.uuid 'delivered' %}",
        ),
        dict(
            label=_("Failed URL"),
            url="https://{{ channel.callback_domain }}{% url 'courier.m3' channel.uuid 'failed' %}",
        ),
    )

    available_timezones = ["Asia/Karachi"]
