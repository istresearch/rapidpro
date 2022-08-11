import base64
import io
import pyqrcode
from uuid import uuid4

from django import forms
from django.core.exceptions import ValidationError
from smartmin.views import SmartFormView

from django.http import HttpResponseRedirect
from django.urls import reverse

from temba import settings
from temba.utils import analytics
from django.utils.translation import ugettext_lazy as _

from ...models import Org

from . import postoffice
from ...models import Channel
from ...views import (
    ALL_COUNTRIES,
    BaseClaimNumberMixin,
    ClaimViewMixin,
)

from engage.utils.strings import is_empty


class ClaimView(BaseClaimNumberMixin, SmartFormView):
    code = "PSM"
    uuid = None
    extra_links = None
    pm_app_url: str = getattr(settings, "POST_MASTER_DL_URL", '')
    pm_app_qrcode: str = getattr(settings, "POST_MASTER_DL_QRCODE", '')

    class Form(ClaimViewMixin.Form):
        CHAT_MODE_CHOICES = getattr(settings, "CHAT_MODE_CHOICES", ())
        device_name = forms.CharField(label="You must provide a Device Name", help_text=_("Postmaster Device Name"))
        device_id = forms.CharField(label="You must provide a Device ID", help_text=_("Postmaster Device ID"))
        chat_mode = forms.ChoiceField(label="Postmaster Chat Mode", help_text=_("Postmaster Chat Mode"),
                                         choices=CHAT_MODE_CHOICES)
        claim_code = forms.CharField(label="Claim Code", help_text=_("Claim Code"))
        org_id = forms.IntegerField(label="Org ID", help_text=_("Org ID"))

        def clean(self):
            device_name = self.cleaned_data.get("device_name", None)
            device_id = self.cleaned_data.get("device_id", None)
            chat_mode = self.cleaned_data.get("chat_mode", None)
            claim_code = self.cleaned_data.get("claim_code", None)
            org_id = self.cleaned_data.get("org_id", None)

            if not device_id:  # pragma: needs cover
                raise ValidationError(_("You must provide a Device ID"))
            if not device_name:
                raise ValidationError(_("You must provide a Device Name"))
            if not chat_mode:
                raise ValidationError(_("You must select a Chat mode"))
            if not claim_code:
                raise ValidationError(_("You must provide a Claim code"))
            if not org_id:
                raise ValidationError(_("You must provide an Org ID"))

            if org_id is not None:
                channel = None
                channels = Channel.objects.filter(channel_type=ClaimView.code, is_active=True)
                for ch in channels:
                    if ch.config.get('chat_mode') == chat_mode and ch.config.get('device_id') == device_id and \
                            ch.org.id == org_id:
                        channel = ch
                        break

                if channel is not None:
                    raise ValidationError(_("A chat mode for {} already exists for the org with ID {}"
                                            .format(dict(self.CHAT_MODE_CHOICES)[chat_mode], org_id)))

            return self.cleaned_data

    def __init__(self, channel_type):
        super().__init__(channel_type)
        self.account = None
        self.client = None

    def get_search_countries_tuple(self):
        if self.channel_type.code == self.code:
            return ["US"]
        else:
            return ALL_COUNTRIES

    def get_supported_countries_tuple(self):
        if self.channel_type.code == self.code:
            return ["US"]
        else:
            return ALL_COUNTRIES

    def get_search_url(self):
        return ""

    def get_claim_url(self):
        return reverse("channels.types.postmaster.claim")

    def init_pm_app_dl(self, request):
        if is_empty(self.pm_app_url) and not is_empty(settings.PM_CONFIG.fetch_url):
            theNonce = settings.PM_CONFIG.get_nonce()
            self.pm_app_url = request.build_absolute_uri(reverse('channels.channel_download_postmaster',
                args=theNonce,
            ))
            qrc = pyqrcode.create(self.pm_app_url)
            qrstream = io.BytesIO()
            qrc.png(qrstream, scale=4)
            self.pm_app_qrcode = f"data:image/png;base64, {base64.b64encode(qrstream.getvalue()).decode('ascii')}"
        #endif
    #enddef init_pm_app_dl

    def get_gear_links(self):
        links = []

        extra_links = self.extra_links
        if extra_links:
            for extra in extra_links:
                links.append(dict(title=extra["name"], href=reverse(extra["link"], args=[self.object.uuid])))

        if self.pm_app_qrcode:
            links.append(
                dict(
                    title="Show App QR",
                    as_btn=True,
                    js_class="mi-pm-app-qr",
                )
            )

        return links

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['po_qr'] = postoffice.fetch_qr_code(self.org)
        self.init_pm_app_dl(self.request)
        context['pm_app_url'] = self.pm_app_url
        context['pm_app_qrcode'] = self.pm_app_qrcode
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
        org_id = form.cleaned_data["org_id"]

        channel = self.create_channel(self.request.user, org_id, Channel.ROLE_SEND + Channel.ROLE_CALL, device_id,
                                      device_name, chat_mode, claim_code)

        self.uuid = channel.uuid
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        analytics.track(user, "temba.channel_claim_postmaster",
                        properties=dict(address=phone_number))
        return None

    def create_channel(self, user, org_id, role, device_id, device_name, chat_mode, claim_code):
        org = Org.objects.filter(id=org_id).first()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()
        config = {
            Channel.CONFIG_DEVICE_NAME: device_name,
            Channel.CONFIG_DEVICE_ID: device_id,
            Channel.CONFIG_CHAT_MODE: chat_mode,
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
            Channel.CONFIG_CLAIM_CODE: claim_code,
            Channel.CONFIG_ORG_ID: org_id
        }

        import temba.contacts.models as Contacts
        prefix = 'PM_'
        if chat_mode == 'SMS':
            prefix = ''

        scheme_to_check = '{}{}_SCHEME'.format(prefix, dict(ClaimView.Form.CHAT_MODE_CHOICES)[chat_mode]).upper()

        schemes = [getattr(Contacts.URN, scheme_to_check)]

        name_with_scheme = '{} [{}]'.format(device_name, schemes[0])

        channel = Channel.create(
            org, user, None, self.code, name=name_with_scheme, address=device_id, role=role, config=config,
            uuid=self.uuid, schemes=schemes
        )

        analytics.track(user, "temba.channel_claim_postmaster", properties=dict(number=device_id))

        return channel
