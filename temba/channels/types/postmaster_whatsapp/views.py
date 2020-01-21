import os
from uuid import uuid4

from django.core.exceptions import ValidationError
from smartmin.views import SmartFormView

from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from ...models import Channel
from ...views import (
    ALL_COUNTRIES,
    TWILIO_SEARCH_COUNTRIES,
    BaseClaimNumberMixin,
    ClaimViewMixin,
)

class ClaimView(BaseClaimNumberMixin, SmartFormView):
    uuid = None

    class Form(ClaimViewMixin.Form):
        pm_claim_code = forms.CharField(label="Claim Code", help_text=_("Claim Code"))
        pm_phone_number = forms.CharField(label="Phone Number (Ex. +14155552671)", help_text=_("Your Device Phone Number"))

        def clean(self):
            pm_claim_code = self.cleaned_data.get("pm_claim_code", None)
            pm_phone_number = self.cleaned_data.get("pm_phone_number", None)

            if not pm_claim_code:  # pragma: needs cover
                raise ValidationError(_("You must enter a claim code"))
            if not pm_phone_number:
                raise ValidationError(_("You must enter your Device's Phone Number"))
            if not str(pm_phone_number).startswith("+"):
                raise ValidationError(_("Please provide a valid E.164 formatted phone number (Ex. +14155552671)"))

            return self.cleaned_data

    def __init__(self, channel_type):
        super().__init__(channel_type)
        self.account = None
        self.client = None

    def get_search_countries_tuple(self):
        return TWILIO_SEARCH_COUNTRIES

    def get_supported_countries_tuple(self):
        return ALL_COUNTRIES

    def get_search_url(self):
        return reverse("channels.channel_search_numbers")

    def get_claim_url(self):
        return reverse("channels.types.bandwidth.claim")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
            return reverse("channels.channel_read", args=[self.uuid])

    form_class = Form
    submit_button_name = "Save"
    success_url = "@channels.types.bandwidth.claim"
    field_config = dict(bw_account_sid=dict(label=""), bw_account_token=dict(label=""))
    success_message = "Bandwidth Account successfully connected."

    def form_valid(self, form):
        pm_claim_code = form.cleaned_data["pm_claim_code"]
        pm_phone_number = form.cleaned_data["pm_phone_number"]

        channel = self.create_channel(self.request.user, Channel.ROLE_SEND + Channel.ROLE_RECEIVE, pm_claim_code, pm_phone_number, "US")

        self.uuid = channel.uuid

        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        return None

    def create_channel(self, user, role, claim_code, phone_number, country):
        from . import PostmasterWhatsAppType
        org = user.get_org()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()
        config = {
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
        }

        channel = Channel.create(
            org, user, country, PostmasterWhatsAppType.code, name=phone_number, address=phone_number, role=role, config=config,
            uuid=self.uuid
        )

        # analytics.track(user.username, "temba.channel_claim_bandwidth", properties=dict(number=phone_number))

        return channel
