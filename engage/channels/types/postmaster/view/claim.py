import base64
import io
import json

import pyqrcode
import requests

from django.conf import settings
from django.urls import reverse

from engage.utils.class_overrides import MonkeyPatcher
from temba.channels.types.postmaster.type import ClaimView

from ..postoffice import (
    po_server_url,
    po_api_key,
    po_api_header,
)
from engage.utils.logs import LogExtrasMixin
from engage.utils.strings import is_empty


class ClaimViewOverrides(MonkeyPatcher, LogExtrasMixin):
    patch_class = ClaimView

    pm_app_url: str = getattr(settings, "POST_MASTER_DL_URL", '')
    pm_app_qrcode: str = getattr(settings, "POST_MASTER_DL_QRCODE", '')
    pm_app_version: str = "unknown"

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

    def fetch_qr_code(self, data):
        if po_server_url is not None and po_api_key is not None:
            user = self.get_user()
            r = requests.post(
                f"{po_server_url}/engage/claim",
                headers={
                    po_api_header: str(po_api_key),
                    "po-api-client-id": str(user.id),
                },
                data=data,
                cookies=None,
                verify=False,
                timeout=10,
            )
            if r.status_code == 200:
                return json.loads(r.content)["data"]
            #endif
        #endif
    #enddef fetch_qr_code

    def get_context_data(self: type[ClaimView], **kwargs):
        context = super(type(self), self).get_context_data(**kwargs)

        name_format = self.request.GET.get('name_format', '{{device_id}} [{{pm_scheme}}]')
        user = self.get_user()
        org = user.get_org()
        data = json.dumps({
            'org_id': org.id,
            'org_name': org.name,
            'created_by': user.id,
            'name_format': name_format,
        })

        context['po_qr'] = self.fetch_qr_code(data)
        self.init_pm_app_dl(self.request)
        context['pm_app_url'] = self.pm_app_url
        context['pm_app_qrcode'] = self.pm_app_qrcode
        context['pm_app_version'] = self.pm_app_version
        context['name_format'] = name_format

        return context
    #enddef get_context_data

#endclass ClaimViewOverrides
