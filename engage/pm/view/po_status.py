import json

import requests
from django.http import HttpRequest, HttpResponse
from django.views import View
from rest_framework import status

from engage.api.responses import HttpResponseNoContent
from engage.utils import get_required_arg
from engage.utils.logs import OrgPermLogInfoMixin

from engage.channels.types.postmaster.postoffice import (
    po_server_url,
    po_api_key,
    po_api_header,
)
from temba.orgs.views import OrgPermsMixin


class PmPostOfficeStatus(OrgPermLogInfoMixin, OrgPermsMixin, View):  # pragma: no cover
    permission = "channels.channel_create"

    @classmethod
    def derive_url_pattern(cls, path, action):
        return r"^%s/%s/(?P<nonce>[^/]+)/$" % (path, action)
    #enddef derive_url_pattern

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        # non authenticated users without orgs get an error (not the org chooser)
        user = self.get_user()
        if not user.is_authenticated:
            return HttpResponse('Not authorized', status=401)
        #endif
        return super().dispatch(request, *args, **kwargs)
    #enddef dispatch

    def post(self, request: HttpRequest, *args, **kwargs):
        return HttpResponse("METHOD not allowed", status=405)
    #enddef post

    def channel_status(self, nonce):
        if po_server_url is not None and po_api_key is not None:
            data = json.dumps({"api_key": nonce})
            r = requests.post(
                f"{po_server_url}/engage/claimUsedBy",
                headers={po_api_header: "{}".format(po_api_key)},
                data=data,
                cookies=None,
                verify=False,
            )
            if r.status_code == status.HTTP_200_OK:
                return json.loads(r.content)["data"]["relayer_id"]
            #endif
        return None
    #enddef channel_status

    def get(self, request: HttpRequest, *args, **kwargs):
        #logger = logging.getLogger()
        #reqData = request.GET

        # ensure we have the necessary args
        try:
            nonce: str = get_required_arg('nonce', kwargs)
        except ValueError as vx:
            return HttpResponse(vx, status=400)
        #endtry

        r = self.channel_status(nonce)
        if r is not None:
            return HttpResponse(json.dumps({
                'msg': 'a device registered with that nonce',
                'device_id': r,
            }), content_type='application/json')
        else:
            return HttpResponseNoContent()
        #endif
    #enddef post

#endclass PmPostOfficeStatus
