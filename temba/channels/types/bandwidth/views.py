from uuid import uuid4

import phonenumbers
from django.core.exceptions import ValidationError
from phonenumbers.phonenumberutil import region_code_for_number
from smartmin.views import SmartFormView
from twilio.base.exceptions import TwilioRestException

from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from temba.orgs.models import BW_ACCOUNT_SID, BW_ACCOUNT_TOKEN, BW_APPLICATION_SID
from temba.utils.timezones import timezone_to_country_code

from ...models import Channel
from ...views import (
    ALL_COUNTRIES,
    TWILIO_SEARCH_COUNTRIES,
    TWILIO_SUPPORTED_COUNTRIES,
    BaseClaimNumberMixin,
    ClaimViewMixin,
)


class ClaimView(BaseClaimNumberMixin, SmartFormView):
    uuid = None

    class Form(ClaimViewMixin.Form):
        bw_account_sid = forms.CharField(label="Account SID", help_text=_("Your Bandwidth Account ID"))
        bw_account_token = forms.CharField(label="Account Token", help_text=_("Your Bandwidth API Token"))
        bw_account_secret = forms.CharField(label="Account Secret", help_text=_("Your Bandwidth API Secret"))
        bw_phone_number = forms.CharField(label="Phone Number", help_text=_("Your Bandwidth Account Phone Number"))
        bw_application_sid = forms.CharField(label="Application SID",
                                             help_text=_("Your Bandwidth Account Application ID"))

        def clean(self):
            from temba.utils.bandwidth import BandwidthRestClient

            bw_account_sid = self.cleaned_data.get("bw_account_sid", None)
            bw_account_token = self.cleaned_data.get("bw_account_token", None)
            bw_account_secret = self.cleaned_data.get("bw_account_secret", None)
            bw_phone_number = self.cleaned_data.get("bw_phone_number", None)
            bw_application_sid = self.cleaned_data.get("bw_application_sid", None)

            if not bw_account_sid:  # pragma: needs cover
                raise ValidationError(_("You must enter your Bandwidth Account ID"))

            if not bw_account_token:
                raise ValidationError(_("You must enter your Bandwidth Account Token"))
            if not bw_account_secret:
                raise ValidationError(_("You must enter your Bandwidth Account Secret"))
            if not bw_phone_number:
                raise ValidationError(_("You must enter your Bandwidth Account's Phone Number"))
            if not bw_application_sid:
                raise ValidationError(_("You must enter your Bandwidth Account's Application ID"))

            bw_phone_number = forms.CharField(help_text=_("Your Bandwidth Account Phone Number"))
            bw_application_sid = forms.CharField(help_text=_("Your Bandwidth Account Application ID"))

            try:
                client = BandwidthRestClient('{}'.format(bw_account_sid), '{}'.format(bw_account_token),
                                             '{}'.format(bw_account_secret), bw_phone_number, bw_application_sid,
                                             client_name='account', api_version='')
                media = client.get_media()
            except Exception:
                raise ValidationError(
                    _("The Bandwidth account credentials seem invalid. Please check them again and retry.")
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
        return reverse("channels.types.bandwidth.claim")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["account_trial"] = self.account.type.lower() == "trial"
        return context

    def get_success_url(self):
            return reverse("channels.channel_read", args=[self.uuid])

    form_class = Form
    submit_button_name = "Save"
    success_url = "@channels.types.bandwidth.claim"
    field_config = dict(bw_account_sid=dict(label=""), bw_account_token=dict(label=""))
    success_message = "Bandwidth Account successfully connected."

    def form_valid(self, form):
        bw_account_sid = form.cleaned_data["bw_account_sid"]
        bw_account_token = form.cleaned_data["bw_account_token"]
        bw_account_secret = form.cleaned_data["bw_account_secret"]
        bw_phone_number = form.cleaned_data["bw_phone_number"]
        bw_application_sid = form.cleaned_data["bw_application_sid"]

        org = self.org
        org.connect_bandwidth(bw_account_sid, bw_account_token, bw_account_secret, bw_phone_number,
                              bw_application_sid, self.request.user)
        org.save()

        channel = self.claim_number(self.request.user, bw_phone_number, "US", Channel.ROLE_SEND + Channel.ROLE_CALL)

        self.uuid = channel.uuid
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        org = user.get_org()
        self.uuid = uuid4()
        client = org.get_bandwidth_messaging_client()
        callback_domain = org.get_brand_domain()
        org_config = org.config
        config = {
            Channel.CONFIG_APPLICATION_SID: org_config[BW_APPLICATION_SID],
            # Channel.CONFIG_NUMBER_SID: number_sid,
            Channel.CONFIG_ACCOUNT_SID: org_config[BW_ACCOUNT_SID],
            Channel.CONFIG_AUTH_TOKEN: org_config[BW_ACCOUNT_TOKEN],
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
        }

        channel = Channel.create(
            org, user, country, "BWD", name=org_config[BW_ACCOUNT_SID], address=phone_number, role=role, config=config, uuid=self.uuid
        )

        # analytics.track(user.username, "temba.channel_claim_twilio", properties=dict(number=phone_number))

        return channel