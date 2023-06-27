from django.utils.translation import gettext_lazy as _

from temba.contacts.models import URN

from ...models import ChannelType
from .views import ClaimView


class ArabiaCellType(ChannelType):
    """
    An ArabiaCell channel type (http://arabiacell.com)
    """

    code = "AC"
    name = "ArabiaCell"
    available_timezones = ["Asia/Amman"]
    recommended_timezones = ["Asia/Amman"]
    category = ChannelType.Category.PHONE
    schemes = [URN.TEL_SCHEME]
    max_length = 1530
    attachment_support = False

    claim_view = ClaimView
    claim_blurb = _("If you have an %(link)s number, you can quickly connect it using their APIs.") % {
        "link": '<a href="https://www.arabiacell.com/">ArabiaCell</a>'
    }

    configuration_blurb = _(
        "To finish connecting your channel, you need to have ArabiaCell configure the URL below for your short code."
    )

    configuration_urls = (
        dict(
            label=_("Receive URL"),
            url="https://{{channel.callback_domain}}/c/ac/{{channel.uuid}}/receive",
            description=_("This URL should be called by ArabiaCell when new messages are received."),
        ),
    )
