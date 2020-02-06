import os
from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from smartmin.views import SmartFormView

from temba.orgs.models import BWI_SENDER, BWI_ENCODING, BWI_USERNAME, BWI_PASSWORD
from temba.utils import analytics
from ...models import Channel
from ...views import (
    ALL_COUNTRIES,
    BaseClaimNumberMixin,
    ClaimViewMixin,
    TWILIO_SEARCH_COUNTRIES)


class ClaimView(BaseClaimNumberMixin, SmartFormView):
    uuid = None

    def pre_process(self, *args, **kwargs):
        org = self.request.user.get_org()
        try:
            self.client = org.get_bandwidth_international_messaging_client()
            if not self.client:
                return HttpResponseRedirect(reverse("orgs.org_bandwidth_international_connect"))
        except Exception:
            return HttpResponseRedirect(reverse("orgs.org_bandwidth_international_connect"))

    class Form(ClaimViewMixin.Form):
        bwi_sender = forms.CharField(max_length=128, label=_("Sender"), help_text=_("Sender (Name or Phone Number)"), required=True)
        bwi_encoding = forms.ChoiceField(choices=[('gsm', "GSM"), ("ucs", "UCS"), ("auto", "Auto Detect")],
                                         label="Messaging Encoding")

        def clean(self):
            BWI_KEY = os.environ.get("BWI_KEY")
            if not BWI_KEY or len(BWI_KEY) == 0:
                raise ValidationError(_("The environment variable BWI_KEY must be a valid encryption key"))

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
        return reverse("channels.types.bandwidth_international.claim")
    
    def get_success_url(self):
            return reverse("channels.channel_read", args=[self.uuid])

    form_class = Form
    submit_button_name = "Save"
    success_url = "@channels.types.bandwidth_international.claim"
    field_config = dict(bw_account_sid=dict(label=""), bw_account_token=dict(label=""))
    success_message = "Bandwidth International account successfully connected."

    def form_valid(self, form):
        bwi_encoding = form.cleaned_data["bwi_encoding"]
        bwi_sender = form.cleaned_data["bwi_sender"]

        channel = self.create_channel(self.request.user, Channel.ROLE_SEND + Channel.ROLE_CALL,
                                      bwi_encoding, bwi_sender)

        self.uuid = channel.uuid
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        analytics.track(user.username, "temba.channel_claim_bandwidth_international",
                        properties=dict(bwi_sender=BWI_SENDER))
        return None

    def create_channel(self, user, role, encoding, bwi_sender):
        org = user.get_org()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()

        config = {
            Channel.CONFIG_USERNAME: org.config.get(BWI_USERNAME, None),
            Channel.CONFIG_PASSWORD: org.config.get(BWI_PASSWORD, None),
            Channel.CONFIG_ENCODING: encoding,
            Channel.CONFIG_SENDER: bwi_sender,
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain
        }

        channel = Channel.create(address=bwi_sender, org=org, user=user, channel_type="BWI", name=bwi_sender,
                                 role=role, config=config, uuid=self.uuid, country="")
        
        channel.config[Channel.CONFIG_KEY] = channel.pk
        channel.save()
        return channel