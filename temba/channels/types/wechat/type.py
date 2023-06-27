from django.utils.translation import gettext_lazy as _

from temba.contacts.models import URN

from ...models import ChannelType
from .views import ClaimView


class WeChatType(ChannelType):
    """
    A WeChat channel (https://www.wechat.com)
    """

    code = "WC"
    category = ChannelType.Category.SOCIAL_MEDIA
    beta_only = True

    courier_url = r"^wc/(?P<uuid>[a-z0-9\-]+)/?$"

    name = "WeChat"
    icon = "icon-wechat"

    claim_blurb = _(
        "Add a %(link)s bot to send and receive messages to WeChat users for free. Your users will need an Android, "
        "Windows or iOS device and a WeChat account to send and receive messages."
    ) % {"link": '<a href="https://wechat.com">WeChat</a>'}
    claim_view = ClaimView

    schemes = [URN.WECHAT_SCHEME]
    max_length = 1600
    attachment_support = False
    free_sending = True

    show_public_addresses = True

    configuration_blurb = _(
        "To finish configuring your WeChat connection, you'll need to enter the following webhook URL and token on "
        "WeChat Official Accounts Platform."
    )

    configuration_urls = (
        dict(label=_("Webhook URL"), url="https://{{ channel.callback_domain }}{% url 'courier.wc' channel.uuid %}"),
        dict(label=_("Token"), url="{{ channel.config.secret }}"),
    )
