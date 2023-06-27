from django.utils.translation import gettext_lazy as _

from temba.channels.views import AuthenticatedExternalClaimView
from temba.contacts.models import URN

from ...models import ChannelType


class BurstSMSType(ChannelType):
    """
    A BurstSMS channel (http://www.burstsms.com.au/)
    """

    code = "BS"
    name = "BurstSMS"
    available_timezones = [
        "Australia/Perth",
        "Australia/Eucla",
        "Australia/Adelaide",
        "Australia/Broken_Hill",
        "Australia/Darwin",
        "Australia/Brisbane",
        "Australia/Currie",
        "Australia/Hobart",
        "Australia/Lindeman",
        "Australia/Melbourne",
        "Australia/Sydney",
        "Australia/Lord_Howe",
        "Pacific/Chatham",
        "Pacific/Auckland",
    ]
    recommended_timezones = available_timezones
    category = ChannelType.Category.PHONE
    schemes = [URN.TEL_SCHEME]
    max_length = 613
    attachment_support = False

    claim_view = AuthenticatedExternalClaimView
    claim_view_kwargs = {
        "username_label": _("API Key"),
        "username_help": _("The API key as found on your settings page"),
        "password_label": _("API Secret"),
        "password_help": _("The API secret as found on your settings page"),
        "form_blurb": _("You can connect your BurstSMS number by entering the settings below."),
    }

    claim_blurb = _("If you have a %(link)s number, you can quickly connect it using their APIs.") % {
        "link": '<a href="https://www.burstsms.com.au/">BurstSMS</a>'
    }

    configuration_blurb = _(
        "To finish connecting your channel, you need to set your callback URLs below for your number."
    )

    configuration_urls = (
        dict(
            label=_("Receive URL"),
            url="https://{{channel.callback_domain}}/c/bs/{{channel.uuid}}/receive",
            description=_(
                "This URL should be called by BurstSMS when new messages are received."
                "You must set this for your number under the 'Inbound Settings' options."
                "Select 'Yes' to the 'Forward to URL' option and enter this URL."
            ),
        ),
        dict(
            label=_("DLR callback URL"),
            url="https://{{channel.callback_domain}}/c/bs/{{channel.uuid}}/status",
            description=_(
                "This URL should be called by BurstSMS when the status of an outgoing message is updated."
                "You can set it on your settings page."
            ),
        ),
        dict(
            label=_("Reply callback URL"),
            url="https://{{channel.callback_domain}}/c/bs/{{channel.uuid}}/receive",
            description=_(
                "This URL should be called by BurstSMS when messages are replied to."
                "You can set it on your settings page."
            ),
        ),
    )
