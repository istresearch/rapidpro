from django.conf import settings
import requests
import json

server_url = getattr(settings, "POST_OFFICE_API_URL", ())
api_key = getattr(settings, "POST_OFFICE_API_KEY", ())


def __init__(self, channel_type):
    super().__init__(channel_type)


def fetch_qr_code(org):
    data = json.dumps({"org_id": org.id, "org_name": org.name})
    if server_url is not None and api_key is not None:
        r = requests.post("{}/engage/claim".format(server_url), headers={"x-api-key": "{}".format(api_key)}, data=data)
        if r.status_code == 200:
            return json.loads(r.content)
    return None


def channel_status(nonce):
    if server_url is not None and api_key is not None:
        data = json.dumps({"api_key": nonce})
        r = requests.post("{}/engage/claimUsedBy".format(server_url), headers={"x-api-key": "{}".format(api_key)}, data=data)
        if r.status_code == 200:
            return json.loads(r.content)["relayer_id"]
    return None

