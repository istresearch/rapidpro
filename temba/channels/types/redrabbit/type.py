from django.utils.translation import gettext_lazy as _

from temba.channels.views import AuthenticatedExternalClaimView
from temba.contacts.models import URN

from ...models import ChannelType


class RedRabbitType(ChannelType):
    """
    A RedRabbit channel (http://www.redrabbitsms.com/)
    """

    code = "RR"
    category = ChannelType.Category.PHONE

    name = "Red Rabbit"

    claim_blurb = _("Easily add a two way number you have configured with %(link)s using their APIs.") % {
        "link": '<a href="http://www.redrabbitsms.com/">Red Rabbit</a>'
    }

    claim_view = AuthenticatedExternalClaimView

    schemes = [URN.TEL_SCHEME]
    max_length = 1600
    attachment_support = False

    def is_available_to(self, user):
        return False, False  # Hidden since it is MT only
