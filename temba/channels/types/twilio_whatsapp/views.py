import phonenumbers
from phonenumbers.phonenumberutil import region_code_for_number
from smartmin.views import SmartFormView
from twilio.base.exceptions import TwilioRestException

from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from temba.channels.types.twilio.views import SUPPORTED_COUNTRIES
from temba.contacts.models import URN
from temba.orgs.models import Org
from temba.utils.fields import SelectWidget
from temba.utils.uuid import uuid4

from ...models import Channel
from ...views import ALL_COUNTRIES, BaseClaimNumberMixin, ClaimViewMixin


class ClaimView(BaseClaimNumberMixin, SmartFormView):
    class Form(ClaimViewMixin.Form):
        country = forms.ChoiceField(choices=ALL_COUNTRIES, widget=SelectWidget(attrs={"searchable": True}))
        phone_number = forms.CharField(help_text=_("The phone number being added"))

        def clean_phone_number(self):
            phone = self.cleaned_data["phone_number"]
            phone = phonenumbers.parse(phone, self.cleaned_data["country"])
            return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)

    form_class = Form

    def __init__(self, channel_type):
        super().__init__(channel_type)
        self.account = None
        self.client = None

    def pre_process(self, *args, **kwargs):
        org = self.request.user.get_org()
        try:
            self.client = org.get_twilio_client()
            if not self.client:
                return HttpResponseRedirect(
                    f'{reverse("orgs.org_twilio_connect")}?claim_type={self.channel_type.slug}'
                )
            self.account = self.client.api.account.fetch()
        except TwilioRestException:
            return HttpResponseRedirect(f'{reverse("orgs.org_twilio_connect")}?claim_type={self.channel_type.slug}')

    def get_search_countries_tuple(self):
        return []

    def get_supported_countries_tuple(self):
        return ALL_COUNTRIES

    def get_search_url(self):
        return ""

    def get_claim_url(self):
        return reverse("channels.types.twilio_whatsapp.claim")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["account_trial"] = self.account.type.lower() == "trial"
        return context

    def get_existing_numbers(self, org):
        client = org.get_twilio_client()
        if client:
            twilio_account_numbers = client.api.incoming_phone_numbers.stream(page_size=1000)

        numbers = []
        for number in twilio_account_numbers:
            parsed = phonenumbers.parse(number.phone_number, None)
            numbers.append(
                dict(
                    number=phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                    country=region_code_for_number(parsed),
                )
            )

        return numbers

    def is_valid_country(self, calling_code: int) -> bool:
        return True

    def is_messaging_country(self, country_code: str) -> bool:
        return country_code in SUPPORTED_COUNTRIES

    def claim_number(self, user, phone_number, country, role):
        org = user.get_org()

        client = org.get_twilio_client()
        twilio_phones = client.api.incoming_phone_numbers.stream(phone_number=phone_number)
        channel_uuid = uuid4()

        # create new TwiML app
        callback_domain = org.get_brand_domain()

        twilio_phone = next(twilio_phones, None)
        if not twilio_phone:
            raise Exception(_("Only existing Twilio WhatsApp number are supported"))

        phone = phonenumbers.format_number(
            phonenumbers.parse(phone_number, None), phonenumbers.PhoneNumberFormat.NATIONAL
        )

        number_sid = twilio_phone.sid

        org_config = org.config
        config = {
            Channel.CONFIG_NUMBER_SID: number_sid,
            Channel.CONFIG_ACCOUNT_SID: org_config[Org.CONFIG_TWILIO_SID],
            Channel.CONFIG_AUTH_TOKEN: org_config[Org.CONFIG_TWILIO_TOKEN],
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
        }

        role = Channel.ROLE_SEND + Channel.ROLE_RECEIVE

        channel = Channel.create(
            org,
            user,
            country,
            self.channel_type,
            name=phone,
            address=phone_number,
            role=role,
            config=config,
            uuid=channel_uuid,
            schemes=[URN.WHATSAPP_SCHEME],
        )

        return channel
