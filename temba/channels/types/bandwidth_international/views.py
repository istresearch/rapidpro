import os
import sys
from uuid import uuid4

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from smartmin.views import SmartFormView

from temba.orgs.models import BWI_ACCOUNT_SID, BWI_APPLICATION_SID, BWI_USER_NAME, BWI_PASSWORD, BWI_ENCODING, \
    BWI_SENDER
from temba.utils import analytics
from temba.utils.bandwidth import AESCipher
from ...models import Channel
from ...views import (
    ALL_COUNTRIES,
    BaseClaimNumberMixin,
    ClaimViewMixin,
    TWILIO_SEARCH_COUNTRIES)
from iris_sdk import Account, Client, RestError


class ClaimView(BaseClaimNumberMixin, SmartFormView):
    uuid = None

    class Form(ClaimViewMixin.Form):
        bwi_account_sid = forms.CharField(label="Account SID", help_text=_("Bandwidth Account ID"))
        bwi_username = forms.CharField(label="Username", help_text=_("Bandwidth Username"))
        bwi_password = forms.CharField(widget=forms.PasswordInput, label="Password", help_text=_("Bandwidth Password"))
        bwi_application_sid = forms.CharField(label="Application SID", help_text=_("Bandwidth Account Application ID"))
        bwi_sender = forms.CharField(max_length=128, label=_("Sender"), help_text=_("Sender (Name or Phone Number)"), required=True)
        bwi_encoding = forms.ChoiceField(choices=[('gsm', "GSM"), ("ucs", "UCS"), ("auto", "Auto Detect")],
                                         label="Messaging Encoding")

        def clean(self):

            bwi_account_sid = self.cleaned_data.get("bwi_account_sid", None)
            bwi_username = self.cleaned_data.get("bwi_username", None)
            bwi_password = self.cleaned_data.get("bwi_password", None)
            bwi_application_sid = self.cleaned_data.get("bwi_application_sid", None)
            bwi_sender = self.cleaned_data.get("bwi_sender", None)
            bwi_encoding = self.cleaned_data.get("bwi_encoding", None)

            if not bwi_account_sid:  # pragma: needs cover
                raise ValidationError(_("You must enter your Bandwidth Account ID"))

            if not bwi_username:
                raise ValidationError(_("You must enter your Bandwidth Account Username"))
            if not bwi_password:
                raise ValidationError(_("You must enter your Bandwidth Account Password"))
            if not bwi_application_sid:
                raise ValidationError(_("You must enter your Bandwidth Account's Application ID"))
            if not bwi_encoding or len(bwi_encoding) == 0:
                raise ValidationError(_("A message encoding must be selected"))
            if not bwi_sender or len(bwi_sender) == 0:
                raise ValidationError(_("A sender must be provided"))

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
    success_message = "Bandwidth Account successfully connected."

    def form_valid(self, form):
        bwi_account_sid = form.cleaned_data["bwi_account_sid"]
        bwi_username = form.cleaned_data["bwi_username"]
        bwi_password = form.cleaned_data["bwi_password"]
        bwi_application_sid = form.cleaned_data["bwi_application_sid"]
        bwi_encoding = form.cleaned_data["bwi_encoding"]
        bwi_sender = form.cleaned_data["bwi_sender"]

        channel = self.create_channel(self.request.user, Channel.ROLE_SEND + Channel.ROLE_CALL, bwi_account_sid,
                                    bwi_username, bwi_password, bwi_application_sid, bwi_encoding, bwi_sender)

        self.uuid = channel.uuid
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        analytics.track(user.username, "temba.channel_claim_bandwidth_international",
                        properties=dict(account_sid=BWI_ACCOUNT_SID))
        return None

    def create_channel(self, user, role, account_sid, username, password, application_sid, encoding, bwi_sender):
        org = user.get_org()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()

        config = {
            Channel.CONFIG_APPLICATION_SID: application_sid,
            Channel.CONFIG_ACCOUNT_SID: account_sid,
            Channel.CONFIG_USERNAME: AESCipher(username, settings.SECRET_KEY).encrypt(),
            Channel.CONFIG_PASSWORD: AESCipher(password, settings.SECRET_KEY).encrypt(),
            Channel.CONFIG_ENCODING: encoding,
            Channel.CONFIG_SENDER: bwi_sender,
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain
        }

        channel = Channel.create(address=bwi_sender, org=org, user=user, channel_type="BWI", name=account_sid,
                                 role=role, config=config, uuid=self.uuid, country="")

        channel.config[Channel.CONFIG_KEY] = channel.pk
        channel.save()
        return channel
