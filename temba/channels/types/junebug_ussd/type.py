from django.utils.translation import ugettext_lazy as _

from temba.channels.models import ChannelType
from temba.channels.types.junebug_ussd.views import ClaimView
from temba.contacts.models import TEL_SCHEME


class JunebugUSSDType(ChannelType):
    """
    A Junebug USSD channel
    """

    code = "JNU"
    category = ChannelType.Category.USSD

    name = "Junebug USSD"
    slug = "junebug_ussd"
    icon = "icon-junebug"

    claim_blurb = _(
        """Connect your <a href="https://junebug.praekelt.org/" target="_blank">Junebug</a> instance that you have already set up and configured."""
    )
    claim_view = ClaimView

    schemes = [TEL_SCHEME]
    max_length = 1600

    configuration_blurb = _(
        """
        As a last step you'll need to configure Junebug to call the following URL for MO (incoming) messages.
        """
    )

    configuration_urls = (
        dict(
            label=_("Push Message URL"),
            url="https://{{ channel.callback_domain }}{% url 'handlers.junebug_handler' 'inbound' channel.uuid %}",
            description=_(
                "This endpoint will be called by Junebug when new messages are received to your number, it must be configured to be called as a POST"
            ),
        ),
    )

    def is_available_to(self, user):
        return False
