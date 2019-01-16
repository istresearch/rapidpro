import logging

import requests

from django.conf import settings

from temba.utils import json

logger = logging.getLogger(__name__)


class MailroomException(Exception):
    """
    Exception for failed requests to mailroom
    """

    def __init__(self, endpoint, request, response):
        self.endpoint = endpoint
        self.request = request
        self.response = response

    def as_json(self):
        return {"endpoint": self.endpoint, "request": self.request, "response": self.response}


class MailroomClient:
    """
    Basic web client for mailroom
    """

    default_headers = {"User-Agent": "Temba"}

    def __init__(self, base_url, auth_token):
        self.base_url = base_url
        self.headers = self.default_headers.copy()
        if auth_token:
            self.headers["Authorization"] = "Token " + auth_token

    def flow_migrate(self, payload):
        return self._request("flow/migrate", payload)

    def sim_start(self, payload):
        return self._request("sim/start", payload)

    def sim_resume(self, payload):
        return self._request("sim/resume", payload)

    def _request(self, endpoint, payload):
        if logger.isEnabledFor(logging.DEBUG):  # pragma: no cover
            logger.debug("=============== %s request ===============" % endpoint)
            logger.debug(json.dumps(payload, indent=2))
            logger.debug("=============== /%s request ===============" % endpoint)

        response = requests.post("%s/mr/%s" % (self.base_url, endpoint), json=payload, headers=self.headers)
        resp_json = response.json()

        if logger.isEnabledFor(logging.DEBUG):  # pragma: no cover
            logger.debug("=============== %s response ===============" % endpoint)
            logger.debug(json.dumps(resp_json, indent=2))
            logger.debug("=============== /%s response ===============" % endpoint)

        if 400 <= response.status_code < 500:
            raise MailroomException(endpoint, payload, resp_json)

        response.raise_for_status()

        return resp_json


def get_client():
    return MailroomClient(settings.MAILROOM_URL, settings.MAILROOM_AUTH_TOKEN)
