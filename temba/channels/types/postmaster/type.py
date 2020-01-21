from django.utils.translation import ugettext_lazy as _

from temba.channels.types.postmaster.views import ClaimView
from temba.contacts.models import TEL_SCHEME

from ...models import ChannelType


##############################################
# Postmaster - WhatsApp channel
##############################################
class PostmasterType(ChannelType):
    code = "PM-WA"
    category = ChannelType.Category.PHONE

    courier_url = r"^pm-wa/(?P<uuid>[a-z0-9\-]+)/(?P<action>receive|status)$"

    name = "Postmaster/WhatsApp"
    icon = "icon-channel-postmaster"
    claim_blurb = _(
        "Send and receive messages over WhatsApp"
    )
    claim_view = ClaimView

    schemes = [TEL_SCHEME]
    max_length = 4096
    attachment_support = True
