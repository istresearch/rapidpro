from django.conf import settings
import requests
import json

po_server_url = getattr(settings, "POST_OFFICE_API_URL", ())
po_api_key = getattr(settings, "POST_OFFICE_API_KEY", ())
po_api_header = "po-api-key"


def __init__(self, channel_type):
    super().__init__(channel_type)


def fetch_qr_code(org):
    data = json.dumps({"org_id": org.id, "org_name": org.name})
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
    return None


def channel_status(nonce):
    if po_server_url is not None and po_api_key is not None:
        data = json.dumps({"api_key": nonce})
        r = requests.post(
            "{}/engage/claimUsedBy".format(po_server_url),
            headers={po_api_header: "{}".format(po_api_key)},
            data=data,
            cookies=None,
            verify=False,
        )
        if r.status_code == 200:
            return json.loads(r.content)["data"]["relayer_id"]
    return None
