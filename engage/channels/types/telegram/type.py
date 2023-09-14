from django import forms
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import MonkeyPatcher

from temba.channels.views import UpdateChannelForm
from temba.channels.types.telegram.type import TelegramType


class UpdateTelegramForm(UpdateChannelForm):

    def add_config_fields(self):
        self.fields["forward_id"] = forms.CharField(
            max_length=255,
            required=False,
            help_text=_("Telegram ID to forward unhandleable messages to"),
            initial=self.instance.config.get("forward_id", ""),
        )
    #enddef add_config_fields

    class Meta(UpdateChannelForm.Meta):
        fields = "name", "address", "country", "alert_email", "tps"
        config_fields = ["forward_id",]
        readonly = ("address")
    #endclass Meta

#endclass UpdateTelegramForm


class TelegramTypeOverrides(MonkeyPatcher):
    patch_class = TelegramType
    update_form = UpdateTelegramForm
#endclass TelegramTypeOverrides
