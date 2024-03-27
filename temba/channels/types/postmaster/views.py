import base64
import io
import logging
import pyqrcode
import traceback
from uuid import uuid4

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponseServerError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from smartmin.views import SmartFormView

from temba.contacts.models import URN as ContactsURN
from temba.utils import analytics

from ...models import Org

from . import postoffice

from ...models import Channel
from ...views import (
    BaseClaimNumberMixin,
    ClaimViewMixin,
    UpdateChannelForm,
)

from engage.utils.logs import LogExtrasMixin
from engage.utils.strings import is_empty


logger = logging.getLogger(__name__)

class ClaimView(LogExtrasMixin, BaseClaimNumberMixin, SmartFormView):
    uuid = None
    extra_links = None
    pm_app_url: str = getattr(settings, "POST_MASTER_DL_URL", '')
    pm_app_qrcode: str = getattr(settings, "POST_MASTER_DL_QRCODE", '')
    pm_app_version: str = "unknown"

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
                channels = Channel.objects.filter(channel_type=self.channel_type, is_active=True, org=org_id,
                                                  config__contains=f'"device_id": "{device_id}"')
                for ch in channels:
                    if ch.config.get('chat_mode') == chat_mode:
                        channel = ch
                        break

                if channel is not None:
                    raise ValidationError(
                        _("A PM chat mode for {} already exists for the device {} and org ID {}".format(
                            dict(self.CHAT_MODE_CHOICES)[chat_mode], device_id, org_id
                        ))
                    )
                #endif

            return self.cleaned_data
        #enddef clean
    #endclass Form

    def __init__(self, channel_type):
        super().__init__(channel_type)
        self.account = None
        self.client = None

    def get_search_countries_tuple(self):
        return ["US"]

    def get_supported_countries_tuple(self):
        return ["US"]

    def get_search_url(self):
        return ""

    def get_claim_url(self):
        return reverse("channels.types.postmaster.claim")

    def init_pm_app_dl(self, request):
        if is_empty(self.pm_app_url) and not is_empty(settings.PM_CONFIG.fetch_url):
            theNonce = settings.PM_CONFIG.get_nonce()
            self.pm_app_url = request.build_absolute_uri(reverse('channels.channel_download_postmaster',
                args=(theNonce,),
            ))
            qrc = pyqrcode.create(self.pm_app_url)
            qrstream = io.BytesIO()
            qrc.png(qrstream, scale=4)
            self.pm_app_qrcode = f"data:image/png;base64, {base64.b64encode(qrstream.getvalue()).decode('ascii')}"

            if settings.PM_CONFIG.pm_info and 'version' in settings.PM_CONFIG.pm_info:
                self.pm_app_version = f"Version {settings.PM_CONFIG.pm_info['version']}"
            elif settings.PM_CONFIG.pm_info:
                self.pm_app_version = f"Failed to get version info: {settings.PM_CONFIG.pm_info}"
            #endif
        #endif
    #enddef init_pm_app_dl

    def get_gear_links(self):
        links = []

        extra_links = self.extra_links
        if extra_links:
            for extra in extra_links:
                links.append(dict(title=extra["name"], href=reverse(extra["link"], args=[self.object.uuid])))
            #endfor
        #endif
        if self.pm_app_qrcode:
            links.append(
                dict(
                    title="Show App QR",
                    as_btn=True,
                    js_class="mi-pm-app-qr",
                )
            )
        #endif
        return links
    #enddef get_gear_links

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['po_qr'] = postoffice.fetch_qr_code(self.org)
        self.init_pm_app_dl(self.request)
        context['pm_app_url'] = self.pm_app_url
        context['pm_app_qrcode'] = self.pm_app_qrcode
        context['pm_app_version'] = self.pm_app_version
        return context

    def get_success_url(self):
        return reverse("pm.postmaster_read", args=[self.uuid])
    #enddef get_success_url

    form_class = Form
    submit_button_name = "Save"
    success_url = "@channels.types.postmaster.claim"
    field_config = dict(device_id=dict(label=""), chat_mode=dict(label=""))
    success_message = "Postmaster Channel successfully created."

    def form_valid(self, form, **kwargs):
        device_id = form.cleaned_data["device_id"]
        device_name = form.cleaned_data["device_name"]
        chat_mode = form.cleaned_data["chat_mode"]
        claim_code = form.cleaned_data["claim_code"]
        org_id = form.cleaned_data["org_id"]
        try:
            roles = Channel.ROLE_SEND + Channel.ROLE_CALL + Channel.ROLE_RECEIVE \
                if chat_mode != 'PM' else Channel.ROLE_USSD
            channel = self.create_channel(self.request.user, org_id, roles,
                device_id, device_name, chat_mode, claim_code,
            )
            self.uuid = channel.uuid
            return HttpResponseRedirect(self.get_success_url())
        except Exception as ex:
            logger.error("creating channel failed", extra=self.with_log_extras({
                'ex': ex,
                'tb': traceback.format_tb(ex.__traceback__),
            }))
            return HttpResponseServerError("Registration failed, please contact a server admin.")
        #endtry
    #enddef form_valid

    def claim_number(self, user, phone_number, country, role):
        analytics.track(user, "temba.channel_claim_postmaster",
                        properties=dict(address=phone_number))
        return None
    #enddef claim_number

    def create_channel(self, user, org_id, roles, device_id, device_name, chat_mode, claim_code):
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

        scheme_to_check = f'{dict(ClaimView.Form.CHAT_MODE_CHOICES)[chat_mode]}_SCHEME'.upper()
        schemes = [getattr(ContactsURN, scheme_to_check)]
        name_with_scheme = f'{device_name} [{schemes[0]}]'

        channel = Channel.create(
            org, user, None, self.channel_type, name=name_with_scheme, address=device_id,
            role=roles, config=config, uuid=self.uuid, schemes=schemes
        )

        analytics.track(user, "temba.channel_claim_postmaster", properties=dict(number=device_id))

        return channel
    #enddef create_channel

#endclass ClaimView


class UpdatePostmasterForm(UpdateChannelForm):

    class Meta(UpdateChannelForm.Meta):
        fields = "name", "address", "schemes", "tps"
        readonly = ("address", "schemes")
        helps = {"schemes": _("The Chat Mode that Postmaster will operate under.")}
        labels = {"schemes": _("Chat Mode")}
    #endclass Meta

#endclass UpdatePostmasterForm
