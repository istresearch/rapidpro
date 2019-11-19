import os
from uuid import uuid4

from django.core.exceptions import ValidationError
from smartmin.views import SmartFormView

from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from temba.utils import analytics
from django.utils.translation import ugettext_lazy as _

from temba.orgs.models import BW_ACCOUNT_SID, BW_ACCOUNT_TOKEN, BW_APPLICATION_SID, BW_ACCOUNT_SECRET

from ...models import Channel
from ...views import (
    ALL_COUNTRIES,
    TWILIO_SEARCH_COUNTRIES,
    BaseClaimNumberMixin,
    ClaimViewMixin,
)

from django.conf import settings
from xml.dom import minidom


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
            if not bw_phone_number or not str(bw_phone_number).startswith("+"):
                raise ValidationError(_("Please provide a valid E.164 formatted phone number (Ex. +14155552671)"))

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
        if self.channel_type.code == "BWD":
            return ["US"]
        else:
            return TWILIO_SEARCH_COUNTRIES

    def get_supported_countries_tuple(self):
        if self.channel_type.code == "BWD":
            return ["US"]
        else:
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
        from iris_sdk.client import Client
        bw_account_sid = form.cleaned_data["bw_account_sid"]
        bw_account_token = form.cleaned_data["bw_account_token"]
        bw_account_secret = form.cleaned_data["bw_account_secret"]
        bw_phone_number = form.cleaned_data["bw_phone_number"]
        bw_application_sid = form.cleaned_data["bw_application_sid"]

        org = self.org
        self.create_channel(bw_account_sid, bw_account_token, bw_account_secret, bw_phone_number,
                            bw_application_sid, self.request.user)
        org.save()

        channel = self.create_channel(self.request.user, Channel.ROLE_SEND + Channel.ROLE_CALL, bw_account_sid,
                                      bw_application_sid,  bw_account_token, bw_account_secret, bw_phone_number, "US")

        self.uuid = channel.uuid
        bw_user = os.environ.get("BANDWIDTH_USER")
        bw_pass = os.environ.get("BANDWIDTH_PASS")
        if bw_user and bw_pass:
            client = Client(url="https://dashboard.bandwidth.com", account_id=bw_account_sid, username=bw_user, password=bw_pass)
            app_info = client.get("/api/accounts/{}/applications/{}".format(bw_account_sid, bw_application_sid))
            if app_info and app_info.content:
                node = minidom.parseString(app_info.content)
                if node and len(node.getElementsByTagName("AppName")) > 0 \
                        and len(node.getElementsByTagName("ApplicationId")) > 0:
                    app_name = node.getElementsByTagName("AppName")[0].firstChild.wholeText
                    app_id = node.getElementsByTagName("ApplicationId")[0].firstChild.wholeText
                    msg_url = "https://{}/c/bwd/{}/receive".format(settings.HOSTNAME, self.uuid)
                    data = "<Application><AppName>{}</AppName><CallbackUrl>{}</CallbackUrl></Application>"\
                        .format(app_name, msg_url)
                    client.put("/api/accounts/{}/applications/{}".format(bw_account_sid, app_id), data=data)
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        analytics.track(user.username, "temba.channel_claim_bandwidth_international",
                        properties=dict(address=phone_number))
        return None

    def create_channel(self, user, role, account_sid, application_sid, account_token, account_secret,
                       phone_number, country):
        org = user.get_org()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()
        config = {
            Channel.CONFIG_APPLICATION_SID: application_sid,
            Channel.CONFIG_ACCOUNT_SID: account_sid,
            Channel.CONFIG_AUTH_TOKEN: account_token,
            Channel.CONFIG_SECRET: account_secret,
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
        }

        channel = Channel.create(
            org, user, country, "BWD", name=account_sid, address=phone_number, role=role, config=config,
            uuid=self.uuid
        )

        analytics.track(user.username, "temba.channel_claim_bandwidth", properties=dict(number=phone_number))

        return channel
