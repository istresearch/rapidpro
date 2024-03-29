import json
import logging
import requests

from engage.utils.class_overrides import MonkeyPatcher

from temba.channels.types.postmaster.postoffice import (
    po_server_url, po_api_key, po_api_header,
)
from temba.channels.types.postmaster.views import ClaimView


logger = logging.getLogger()

class ClaimViewOverrides(MonkeyPatcher):
    patch_class = ClaimView

    def fetch_qr_code(self, data):
        if po_server_url is not None and po_api_key is not None:
            r = requests.post(
                "{}/engage/claim".format(po_server_url),
                headers={po_api_header: "{}".format(po_api_key)},
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

    def get_context_data(self: type(ClaimView), **kwargs):
        context = super(ClaimView, self).get_context_data(**kwargs)

        name_format = self.request.GET.get('name_format', '{{device_id}} [{{pm_scheme}}]')
        user = self.get_user()
        data = json.dumps({
            'org_id': self.org.id,
            'org_name': self.org.name,
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
