import telegram

from django import forms
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from temba.contacts.models import TELEGRAM_SCHEME

from ...models import ChannelType
from ...views import UpdateChannelForm
from .views import ClaimView

class UpdateTelegramForm(UpdateChannelForm):

    def add_config_fields(self):
        self.fields["forward_id"] = forms.CharField(max_length=255, required=False, help_text=_("Telegram ID to forward unhandleable messages to"), initial=self.instance.config.get("forward_id",""))

    class Meta(UpdateChannelForm.Meta):
        fields = "name", "address", "country", "alert_email"
        config_fields = ["forward_id",]
        readonly = ("address","country")

class TelegramType(ChannelType):
    """
    A Telegram bot channel
    """

    code = "TG"
    category = ChannelType.Category.SOCIAL_MEDIA

    update_form = UpdateTelegramForm

    courier_url = r"^tg/(?P<uuid>[a-z0-9\-]+)/receive$"

    name = "Telegram"
    icon = "icon-telegram"
    show_config_page = False

    claim_blurb = _(
        """Add a <a href="https://telegram.org">Telegram</a> bot to send and receive messages to Telegram
    users for free. Your users will need an Android, Windows or iOS device and a Telegram account to send and receive
    messages."""
    )
    claim_view = ClaimView

    schemes = [TELEGRAM_SCHEME]
    max_length = 1600
    attachment_support = True
    free_sending = True

    redact_response_keys = {"first_name", "last_name", "username"}

    def activate(self, channel):
        config = channel.config
        bot = telegram.Bot(config["auth_token"])
        bot.set_webhook("https://" + channel.callback_domain + reverse("courier.tg", args=[channel.uuid]))

    def deactivate(self, channel):
        config = channel.config
        bot = telegram.Bot(config["auth_token"])
        bot.delete_webhook()
