from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from smartmin.views import SmartFormView

from django.http import HttpResponseRedirect
from django.urls import reverse
from temba.utils import analytics
from django.utils.translation import ugettext_lazy as _


from ...models import Channel
from ...views import (
    ALL_COUNTRIES,
    TWILIO_SEARCH_COUNTRIES,
    BaseClaimNumberMixin,
    ClaimViewMixin,
)


class ClaimView(BaseClaimNumberMixin, SmartFormView):
    code = "PSMS"
    uuid = None

    class Form(ClaimViewMixin.Form):
        CHAT_MODE_CHOICES = (("WA", _("WhatsApp")), ("TG", _("Telegram")), ("SMS", _("SMS")))
        pm_receiver_id = forms.CharField(label="You must provide a Receiver ID", help_text=_("Postmaster Receiver ID"))
        pm_mode = forms.ChoiceField(label="Postmaster Chat Mode", help_text=_("Postmaster Chat Mode"),
                                    choices=CHAT_MODE_CHOICES)
        def clean(self):

            pm_receiver_id = self.cleaned_data.get("pm_receiver_id", None)
            pm_chat_mode = self.cleaned_data.get("pm_chat_mode", None)

            if not pm_receiver_id:  # pragma: needs cover
                raise ValidationError(_("You must provide a Receiver ID"))
            if not pm_chat_mode:
                raise ValidationError(_("You must select a chat mode"))

            return self.cleaned_data

    def __init__(self, channel_type):
        super().__init__(channel_type)
        self.account = None
        self.client = None

    def get_search_countries_tuple(self):
        if self.channel_type.code == self.code:
            return ["US"]
        else:
            return TWILIO_SEARCH_COUNTRIES

    def get_supported_countries_tuple(self):
        if self.channel_type.code == self.code:
            return ["US"]
        else:
            return ALL_COUNTRIES

    def get_search_url(self):
        return reverse("channels.channel_search_numbers")

    def get_claim_url(self):
        return reverse("channels.types.postmaster.claim")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
            return reverse("channels.channel_read", args=[self.uuid])

    form_class = Form
    submit_button_name = "Save"
    success_url = "@channels.types.postmaster.claim"
    field_config = dict(pm_receiver_id=dict(label=""), pm_chat_mode=dict(label=""))
    success_message = "Postmaster Channel successfully created."

    def form_valid(self, form):
        pm_receiver_id = form.cleaned_data["pm_receiver_id"]
        pm_chat_mode = form.cleaned_data["pm_chat_mode"]

        channel = self.create_channel(self.request.user, Channel.ROLE_SEND + Channel.ROLE_CALL, pm_receiver_id, pm_chat_mode)

        self.uuid = channel.uuid
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        analytics.track(user.username, "temba.channel_claim_postmaster",
                        properties=dict(address=phone_number))
        return None

    def create_channel(self, user, role, pm_receiver_id, pm_chat_mode):
        org = user.get_org()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()
        config = {
            Channel.CONFIG_RECEIVER_ID: pm_receiver_id,
            Channel.CONFIG_CHAT_MODE: pm_chat_mode,
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
        }

        channel = Channel.create(
            org, user, "US", self.code, name=pm_receiver_id, address=pm_receiver_id, role=role, config=config,
            uuid=self.uuid
        )

        analytics.track(user.username, "temba.channel_claim_postmaster", properties=dict(number=pm_receiver_id))

        return channel
