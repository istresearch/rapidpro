from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from smartmin.views import SmartFormView

from django.http import HttpResponseRedirect
from django.urls import reverse

from temba.utils import analytics
from django.utils.translation import ugettext_lazy as _

from django.conf import settings

from . import postoffice
from ...models import Channel
from ...views import (
    ALL_COUNTRIES,
    TWILIO_SEARCH_COUNTRIES,
    BaseClaimNumberMixin,
    ClaimViewMixin,
)


class ClaimView(BaseClaimNumberMixin, SmartFormView):
    code = "PSM"
    uuid = None

    class Form(ClaimViewMixin.Form):
        CHAT_MODE_CHOICES = getattr(settings, "CHAT_MODE_CHOICES", ())
        device_name = forms.CharField(label="You must provide a Device Name", help_text=_("Postmaster Device Name"))
        device_id = forms.CharField(label="You must provide a Device ID", help_text=_("Postmaster Device ID"))
        chat_mode = forms.ChoiceField(label="Postmaster Chat Mode", help_text=_("Postmaster Chat Mode"),
                                         choices=CHAT_MODE_CHOICES)
        claim_code = forms.CharField(label="Claim Code", help_text=_("Claim Code"))

        def clean(self):

            device_name = self.cleaned_data.get("device_name", None)
            device_id = self.cleaned_data.get("device_id", None)
            chat_mode = self.cleaned_data.get("chat_mode", None)
            claim_code = self.cleaned_data.get("claim_code", None)

            if not device_id:  # pragma: needs cover
                raise ValidationError(_("You must provide a Device ID"))
            if not device_name:
                raise ValidationError(_("You must provide a Device Name"))
            if not chat_mode:
                raise ValidationError(_("You must select a Chat mode"))
            if not claim_code:
                raise ValidationError(_("You must provide a Claim code"))

            org = self.request.user.get_org()
            if org is not None:
                channel = None
                channels = Channel.objects.filter(channel_type=ClaimView.code, is_active=True)
                for ch in channels:
                    if ch.config.get('chat_mode') == chat_mode and ch.config.get('device_id') == device_id and \
                            ch.org.id == org.id:
                        channel = ch
                        break

                if channel is not None:
                    raise ValidationError(_("A chat mode for {} already exists for the {} org"
                                            .format(dict(self.CHAT_MODE_CHOICES)[chat_mode], org.name)))

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
        context['po_qr'] = postoffice.fetch_qr_code(self.org)
        return context

    def get_success_url(self):
            return reverse("channels.channel_read", args=[self.uuid])

    form_class = Form
    submit_button_name = "Save"
    success_url = "@channels.types.postmaster.claim"
    field_config = dict(device_id=dict(label=""), chat_mode=dict(label=""))
    success_message = "Postmaster Channel successfully created."

    def form_valid(self, form):
        device_id = form.cleaned_data["device_id"]
        device_name = form.cleaned_data["device_name"]
        chat_mode = form.cleaned_data["chat_mode"]
        claim_code = form.cleaned_data["claim_code"]

        channel = self.create_channel(self.request.user, Channel.ROLE_SEND + Channel.ROLE_CALL, device_id,
                                      device_name, chat_mode, claim_code)

        self.uuid = channel.uuid
        channel.config['org_id'] = channel.org.id
        channel.save()
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        analytics.track(user.username, "temba.channel_claim_postmaster",
                        properties=dict(address=phone_number))
        return None

    def create_channel(self, user, role, device_id, device_name, chat_mode, claim_code):
        org = user.get_org()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()
        config = {
            Channel.CONFIG_DEVICE_NAME: device_name,
            Channel.CONFIG_DEVICE_ID: device_id,
            Channel.CONFIG_CHAT_MODE: chat_mode,
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
            Channel.CONFIG_CLAIM_CODE: claim_code,
        }

        import temba.contacts.models as Contacts
        prefix = ''
        if chat_mode == 'SMS':
            prefix = ''

        kwargs = {'claim_code': claim_code}

        schemes = [getattr(Contacts,
                           '{}{}_SCHEME'.format(prefix, dict(ClaimView.Form.CHAT_MODE_CHOICES)[chat_mode]).upper())]
        channel = Channel.create(
            org, user, None, self.code, name=device_name, address=device_id, role=role, config=config,
            uuid=self.uuid, schemes=schemes, kwargs=kwargs
        )

        analytics.track(user.username, "temba.channel_claim_postmaster", properties=dict(number=device_id))

        return channel
