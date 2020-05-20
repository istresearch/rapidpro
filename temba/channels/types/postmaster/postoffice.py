from django.conf import settings
import requests
import json


def __init__(self, channel_type):
    super().__init__(channel_type)


def fetch_qr_code(org):
    server_url = getattr(settings, "POST_OFFICE_QR_URL", ())
    api_key = getattr(settings, "POST_OFFICE_API_KEY", ())
    data = json.dumps({"org_id": org.id, "org_name": org.name})
    if server_url is not None and api_key is not None:
        r = requests.post(server_url, headers={"x-api-key": "{}".format(api_key)}, data=data)
        if r.status_code == 200:
            return json.loads(r.content)
    return None

