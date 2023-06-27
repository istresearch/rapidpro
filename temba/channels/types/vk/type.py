from django.utils.translation import gettext_lazy as _

from temba.contacts.models import URN

from ...models import ChannelType
from .views import ClaimView

CONFIG_COMMUNITY_NAME = "community_name"
CONFIG_CALLBACK_VERIFICATION_STRING = "callback_verification_string"


class VKType(ChannelType):
    """
    A VK channel
    """

    code = "VK"
    category = ChannelType.Category.SOCIAL_MEDIA

    CONFIG_COMMUNITY_NAME = "community_name"

    courier_url = r"^vk/(?P<uuid>[a-z0-9\-]+)/receive"

    name = "VK"
    icon = "icon-vk"

    claim_blurb = _(
        "Add a %(link)s bot to send and receive messages on behalf of a VK community for free. You will need to create "
        "an access token for your community first."
    ) % {"link": '<a href="https://vk.com/">VK</a>'}
    claim_view = ClaimView

    schemes = [URN.VK_SCHEME]
    max_length = 320
    attachment_support = True
    free_sending = True
