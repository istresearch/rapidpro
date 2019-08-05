import time

import nexmo

from django.urls import reverse


class CustomClient(nexmo.Client):
    """
    TODO: do we still need this?
    """

    def parse(self, host, response):  # pragma: no cover
        # Nexmo client doesn't extend object, so can't call super
        if response.status_code == 401:
            raise nexmo.AuthenticationError
        elif response.status_code == 204:  # pragma: no cover
            return None
        elif 200 <= response.status_code < 300:
            return response.json()
        elif 400 <= response.status_code < 500:  # pragma: no cover
            message = "{code} response from {host}".format(code=response.status_code, host=host)
            raise nexmo.ClientError(message)
        elif 500 <= response.status_code < 600:  # pragma: no cover
            message = "{code} response from {host}".format(code=response.status_code, host=host)
            raise nexmo.ServerError(message)


class Client:
    """
    Wrapper for the actual Nexmo client that adds some functionality and retries
    """

    RATE_LIMIT_PAUSE = 2

    def __init__(self, api_key, api_secret):
        self.base = CustomClient(api_key, api_secret)

    def check_credentials(self):
        try:
            self.base.get_balance()
            return True
        except nexmo.AuthenticationError:
            return False

    def get_numbers(self, pattern=None, size=10):
        params = {"size": size}
        if pattern:
            params["pattern"] = str(pattern).strip("+")

        response = self._with_retry("get_account_numbers", params=params)

        return response["numbers"] if int(response.get("count", 0)) else []

    def search_numbers(self, country, pattern):
        response = self.base.get_available_numbers(
            country_code=country, pattern=pattern, search_pattern=1, features="SMS", country=country
        )
        numbers = []
        if int(response.get("count", 0)):
            numbers += response["numbers"]

        response = self.base.get_available_numbers(
            country_code=country, pattern=pattern, search_pattern=1, features="VOICE", country=country
        )
        if int(response.get("count", 0)):
            numbers += response["numbers"]

        return numbers

    def buy_number(self, country, number):
        params = dict(msisdn=number.lstrip("+"), country=country)

        self._with_retry("buy_number", params=params)

    def update_number(self, country, number, mo_url, app_id):
        number = number.lstrip("+")
        params = dict(
            moHttpUrl=mo_url, msisdn=number, country=country, voiceCallbackType="app", voiceCallbackValue=app_id
        )

        self._with_retry("update_number", params=params)

    def create_application(self, domain, channel_uuid):
        name = "%s/%s" % (domain, channel_uuid)
        answer_url = reverse("handlers.nexmo_call_handler", args=["answer", channel_uuid])
        event_url = reverse("handlers.nexmo_call_handler", args=["event", channel_uuid])

        response = self._with_retry(
            "create_application",
            params={
                "name": name,
                "type": "voice",
                "answer_url": f"https://{domain}{answer_url}",
                "answer_method": "POST",
                "event_url": f"https://{domain}{event_url}",
                "event_method": "POST",
            },
        )

        app_id = response.get("id")
        app_private_key = response.get("keys", {}).get("private_key")
        return app_id, app_private_key

    def delete_application(self, app_id):
        self._with_retry("delete_application", application_id=app_id)

    def _with_retry(self, action, **kwargs):
        """
        Utility to perform something using the Nexmo API, and if it errors with a rate-limit response, try again
        after a small delay.
        """
        func = getattr(self.base, action)

        try:
            return func(**kwargs)
        except nexmo.ClientError as e:
            message = str(e)
            if message.startswith("420") or message.startswith("429"):
                time.sleep(Client.RATE_LIMIT_PAUSE)
                return func(**kwargs)
            else:  # pragma: no cover
                raise e
