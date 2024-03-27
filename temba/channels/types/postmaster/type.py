from django.utils.translation import gettext_lazy as _

from temba.channels.types.postmaster.views import ClaimView, UpdatePostmasterForm

from .. import TYPES as SchemeTypes

from ...models import ChannelType


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
    _scheme = schemes
    max_length = 1600

    update_form = UpdatePostmasterForm

    def deactivate(self, channel):
        number_update_args = dict()

        if not channel.is_delegate_sender():
            number_update_args["sms_application_sid"] = ""

        if channel.supports_ivr():
            number_update_args["voice_application_sid"] = ""

    @property
    def schemes(self):
        for stype in SchemeTypes:
            if self._scheme is not None and stype.name.lower() == self._scheme.lower():
                self.update_form = UpdatePostmasterForm
        return self._scheme

    @schemes.setter
    def set_schemes(self, value):
        self.schemes = _scheme = value
