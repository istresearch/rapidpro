import os
import sys
from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
from smartmin.views import SmartFormView

from temba.orgs.models import BWI_ACCOUNT_SID, BWI_APPLICATION_SID, BWI_USER_NAME, BWI_PASSWORD
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
        # bw_phone_number = forms.CharField(label="Phone Number", help_text=_("Your Bandwidth Account Phone Number"))

        def clean(self):

            bwi_account_sid = self.cleaned_data.get("bwi_account_sid", None)
            bwi_username = self.cleaned_data.get("bwi_username", None)
            bwi_password = self.cleaned_data.get("bwi_password", None)
            bwi_application_sid = self.cleaned_data.get("bwi_application_sid", None)

            BWI_KEY = os.environ.get("BWI_KEY")

            if not bwi_account_sid:  # pragma: needs cover
                raise ValidationError(_("You must enter your Bandwidth Account ID"))

            if not bwi_username:
                raise ValidationError(_("You must enter your Bandwidth Account Username"))
            if not bwi_password:
                raise ValidationError(_("You must enter your Bandwidth Account Password"))
            if not bwi_application_sid:
                raise ValidationError(_("You must enter your Bandwidth Account's Application ID"))
            if not BWI_KEY or len(BWI_KEY) == 0:
                raise ValidationError(_("The environment variable BWI_KEY  must be a valid encryption key"))

            try:
                account = Account(client=Client(url="https://dashboard.bandwidth.com/api", username=bwi_username,
                                      password=bwi_password, account_id=bwi_account_sid)).get(bwi_account_sid)
            except RestError as error:
                raise ValidationError(
                    _(escape(error))
                )
            except Exception as error:
                raise ValidationError(
                    _(escape(error))
                )

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

        org = self.org

        org.connect_bandwidth_international(bwi_account_sid, bwi_username, bwi_password,
                                            bwi_application_sid, self.request.user)
        org.save()

        channel = self.claim_number(self.request.user, Channel.ROLE_SEND + Channel.ROLE_CALL)

        self.uuid = channel.uuid
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, role):
        org = user.get_org()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()
        bwi_key = os.environ.get("BWI_KEY")
        org_config = org.config

        username = AESCipher(org_config[BWI_USER_NAME], bwi_key).encrypt()
        password = AESCipher(org_config[BWI_PASSWORD], bwi_key).encrypt()

        config = {
            Channel.CONFIG_APPLICATION_SID: org_config[BWI_APPLICATION_SID],
            Channel.CONFIG_ACCOUNT_SID: org_config[BWI_ACCOUNT_SID],
            Channel.CONFIG_USERNAME: username,
            Channel.CONFIG_PASSWORD: password,
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
        }

        channel = Channel.create(
            org=org, user=user, channel_type="BWI", name=org_config[BWI_ACCOUNT_SID],
            role=role, config=config, uuid=self.uuid, country=""
        )

        analytics.track(user.username, "temba.channel_claim_bandwidth_international",
                        properties=dict(account_sid=BWI_ACCOUNT_SID))
        return channel