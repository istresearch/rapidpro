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

    def pre_process(self, *args, **kwargs):
        org = self.request.user.get_org()
        try:
            self.client = org.get_bandwidth_messaging_client()
            if not self.client:
                return HttpResponseRedirect(reverse("orgs.org_bandwidth_connect"))
        except Exception:
            return HttpResponseRedirect(reverse("orgs.org_bandwidth_connect"))

    class Form(ClaimViewMixin.Form):
        bw_phone_number = forms.CharField(label="Phone Number (Ex. +14155552671)",
                                          help_text=_("Your Bandwidth Account Phone Number"))

        def clean(self):
            bw_phone_number = self.cleaned_data.get("bw_phone_number", None)

            if not bw_phone_number or not str(bw_phone_number).startswith("+"):
                raise ValidationError(_("Please provide a valid E.164 formatted phone number (Ex. +14155552671)"))
            return self.cleaned_data

    def __init__(self, channel_type):
        super().__init__(channel_type)
        self.account = None
        self.client = None

    def get_search_countries_tuple(self):
        return ["US"]

    def get_supported_countries_tuple(self):
        return ["US"]

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
        bw_phone_number = form.cleaned_data["bw_phone_number"]
        org = self.request.user.get_org()
        config = org.config

        bw_account_sid = config[BW_ACCOUNT_SID]
        bw_application_sid = config[BW_APPLICATION_SID]
        channel = self.create_channel(self.request.user, Channel.ROLE_SEND + Channel.ROLE_CALL, bw_account_sid,
                                      bw_application_sid, config[BW_ACCOUNT_TOKEN], config[BW_ACCOUNT_SECRET],
                                      bw_phone_number, "US")
        self.uuid = channel.uuid
        self.set_callback_url(bw_account_sid, bw_application_sid)

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

    # if channel is created, and dashboard credentials are present, then set the callback URL in BW dashboard
    def set_callback_url(self, bw_account_sid, bw_application_sid):
        from iris_sdk.client import Client
        bw_user = os.environ.get("BANDWIDTH_USER")
        bw_pass = os.environ.get("BANDWIDTH_PASS")
        if bw_user and bw_pass:
            client = Client(url="https://dashboard.bandwidth.com", account_id=bw_account_sid, username=bw_user,
                            password=bw_pass)
            app_info = client.get("/api/accounts/{}/applications/{}".format(bw_account_sid, bw_application_sid))
            if app_info and app_info.content:
                node = minidom.parseString(app_info.content)
                if node and len(node.getElementsByTagName("AppName")) > 0 \
                        and len(node.getElementsByTagName("ApplicationId")) > 0:
                    app_name = node.getElementsByTagName("AppName")[0].firstChild.wholeText
                    app_id = node.getElementsByTagName("ApplicationId")[0].firstChild.wholeText
                    msg_url = "https://{}/c/bwd/{}/receive".format(settings.HOSTNAME, self.uuid)
                    data = "<Application><AppName>{}</AppName><CallbackUrl>{}</CallbackUrl></Application>" \
                        .format(app_name, msg_url)
                    client.put("/api/accounts/{}/applications/{}".format(bw_account_sid, app_id), data=data)
