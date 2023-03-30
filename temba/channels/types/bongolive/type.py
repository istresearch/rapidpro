from django.utils.translation import gettext_lazy as _

from temba.contacts.models import URN

from ...models import ChannelType
from .views import ClaimView


class BongoLiveType(ChannelType):
    """
    An Bongo Live channel type (https://www.bongolive.co.tz)
    """

    code = "BL"
    name = "Bongo Live"
    available_timezones = ["Africa/Dar_es_Salaam"]
    category = ChannelType.Category.PHONE

    courier_url = r"^bl/(?P<uuid>[a-z0-9\-]+)/receive$"

    schemes = [URN.TEL_SCHEME]
    max_length = 160
    attachment_support = False

    claim_view = ClaimView
    claim_blurb = _("If you have an %(link)s number, you can quickly connect it using their APIs.") % {
        "link": '<a href="https://www.bongolive.co.tz/">Bongo Live</a>'
    }

    configuration_blurb = _(
        "To finish connecting your channel, you need to have Bongo Live configure the URLs below for your short code."
    )

    configuration_urls = (
        dict(
            label=_("Receive URL"),
            url="https://{{channel.callback_domain}}/c/bl/{{channel.uuid}}/receive",
            description=_(
                "This URL should be called by Bongo Live when new messages are received or to report DLR status."
            ),
        ),
    )
