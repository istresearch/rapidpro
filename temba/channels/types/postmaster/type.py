from django.utils.translation import gettext_lazy as _

from ...models import ChannelType

from engage.channels.types.postmaster.view.claim import ClaimView


class PostmasterType(ChannelType):
    """
    Postmaster channel
    """

    code = "PSM"
    category = ChannelType.Category.PHONE

    courier_url = r"^psms/(?P<uuid>[a-z0-9\-]+)/(?P<action>receive|status)$"

    name = "Postmaster"
    icon = "icon-tembatoo-postmaster"
    claim_blurb = _(
        """Use Postmaster compatible Android devices"""
    )
    claim_view = ClaimView

    show_config_page = False

    schemes = None
    max_length = 1600

    def deactivate(self, channel):
        number_update_args = dict()

        if not channel.is_delegate_sender():
            number_update_args["sms_application_sid"] = ""
        #endif
        if channel.supports_ivr():
            number_update_args["voice_application_sid"] = ""
        #endif
    #enddef deactivate

#endclass PostmasterType
