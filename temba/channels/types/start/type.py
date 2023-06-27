from django.utils.translation import gettext_lazy as _

from temba.channels.views import AuthenticatedExternalClaimView
from temba.contacts.models import URN

from ...models import ChannelType


class StartType(ChannelType):
    """
    An Start Mobile channel (https://bulk.startmobile.ua/)
    """

    code = "ST"
    category = ChannelType.Category.PHONE

    courier_url = r"^st/(?P<uuid>[a-z0-9\-]+)/(?P<action>receive)$"

    name = "Start Mobile"

    claim_blurb = _("Easily add a two way number you have configured with %(link)s using their APIs.") % {
        "link": '<a href="https://bulk.startmobile.ua/">Start Mobile</a>'
    }
    claim_view = AuthenticatedExternalClaimView

    schemes = [URN.TEL_SCHEME]
    max_length = 1600

    attachment_support = False

    configuration_blurb = _(
        "To finish configuring your Start connection you'll need to notify Start of the following receiving URL."
    )

    configuration_urls = (
        dict(
            label=_("Inbound URL"),
            url="https://{{ channel.callback_domain }}{% url 'courier.st' channel.uuid 'receive' %}",
            description=_("This endpoint should be called by Start when new messages are received to your number."),
        ),
    )

    available_timezones = ["Europe/Kiev"]
