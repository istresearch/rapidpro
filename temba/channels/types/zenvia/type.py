from django.utils.translation import gettext_lazy as _

from temba.channels.models import ChannelType
from temba.channels.types.zenvia.views import ClaimView
from temba.contacts.models import URN


class ZenviaType(ChannelType):
    """
    An Zenvia channel (https://www.zenvia.com/)
    """

    code = "ZV"
    category = ChannelType.Category.PHONE

    courier_url = r"^zv/(?P<uuid>[a-z0-9\-]+)/(?P<action>status|receive)$"

    name = "Zenvia"

    claim_blurb = _(
        "If you are based in Brazil, you can purchase a short code from %(link)s and connect it in a few simple steps."
    ) % {"link": '<a href="http://www.zenvia.com.br/">Zenvia</a>'}
    claim_view = ClaimView

    schemes = [URN.TEL_SCHEME]
    max_length = 150

    available_timezones = ["America/Sao_Paulo"]

    attachment_support = False

    configuration_blurb = _(
        "To finish configuring your Zenvia connection you'll need to set the following callback URLs on your Zenvia "
        "account."
    )

    configuration_urls = (
        dict(
            label=_("Status URL"),
            url="https://{{ channel.callback_domain }}{% url 'courier.zv' channel.uuid 'status' %}",
            description=_(
                "To receive delivery and acknowledgement of sent messages, you need to set the status URL for your "
                "Zenvia account."
            ),
        ),
        dict(
            label=_("Receive URL"),
            url="https://{{ channel.callback_domain }}{% url 'courier.zv' channel.uuid 'receive' %}",
            description=_("To receive incoming messages, you need to set the receive URL for your Zenvia account."),
        ),
    )

    def is_available_to(self, user):
        return False, False
