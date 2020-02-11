
from django.utils.translation import ugettext_lazy as _

from temba.channels.types.postmaster.views import ClaimView
from temba.contacts.models import TEL_SCHEME

from ...models import ChannelType


class PostmasterType(ChannelType):
    """
    An IST Postmaster channel
    """

    code = "PSM"
    category = ChannelType.Category.PHONE

    courier_url = r"^psms/(?P<uuid>[a-z0-9\-]+)/(?P<action>receive|status)$"

    name = "Postmaster"
    icon = "icon-channel-postmaster"
    claim_blurb = _(
        """Use Postmaster compatible android devices with Pulse Engage"""
    )
    claim_view = ClaimView

    schemes = [TEL_SCHEME]
    max_length = 1600

    def deactivate(self, channel):
        number_update_args = dict()

        if not channel.is_delegate_sender():
            number_update_args["sms_application_sid"] = ""

        if channel.supports_ivr():
            number_update_args["voice_application_sid"] = ""
