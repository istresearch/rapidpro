import requests
from urllib.parse import urlencode
from bandwidth import account, messaging, voice, version

from django.utils.encoding import force_text

from temba.utils.http import HttpEvent


def encode_atom(atom):  # pragma: no cover
    if isinstance(atom, (int, bytes)):
        return atom
    elif isinstance(atom, str):
        return atom.encode("utf-8")
    else:
        raise ValueError("list elements should be an integer, " "binary, or string")


class BandwidthRestClient(account.client_module.Client):  # pragma: no cover
    bw_phone_number = None
    bw_application_sid = None
    bw_account_secret = None
    bw_account_token = None

    def __init__(self, user_id=None, api_token=None, api_secret=None, phone_number=None, application_sid=None,  **other_options):
        super().__init__(user_id, api_token, api_secret, **other_options,
                         api_endpoint='https://messaging.bandwidth.com')
        self.bw_phone_number = phone_number
        self.bw_application_sid = application_sid
        self.bw_account_token = api_token
        self.bw_account_secret = api_secret
        self.events = []

    def _request(self, method, url, *args, **kwargs):
        user_agent = 'PythonSDK_' + version.__version__
        headers = kwargs.pop('headers', None)
        if headers:
            headers['User-Agent'] = user_agent
        else:
            headers = {
                'User-Agent': user_agent
            }
        if url.startswith('/'):
            # relative url
            if len(self.api_version) > 0:
                url = '%s/%s%s' % (self.api_endpoint, self.api_version, url)
            else:
                url = '%s%s' % (self.api_endpoint, url)
        return requests.request(method, url, auth=self.auth, headers=headers, *args, **kwargs)

    # https: // dashboard.bandwidth.com / api / accounts / {{accountId}} / applications
    def get_applications(self):
        """
        Get an Applications object

        :rtype: dict
        :returns: applications list

        Example::

            data = api.get_applications()
        """

        return self._make_request('get', '/api/accounts/%s/applications' % self.user_id)[0]

    def get_media(self):
        """
                Get an Media object

                :rtype: dict
                :returns: media list

                Example::

                    data = api.get_media()
                """
        return self._make_request('get', '/api/v2/users/%s/media' % self.user_id)[0]

    def get_account(self):
        """
        Get an Account object

        :rtype: dict
        :returns: account data

        Example::

            data = api.get_account()
        """
        return self._make_request('get', '/users/%s/account' % self.user_id)[0]

    def request(self, method, uri, **kwargs):
        data = kwargs.get("data")
        if data is not None:
            udata = {}
            for k, v in data.items():
                key = k.encode("utf-8")
                if isinstance(v, (list, tuple, set)):
                    udata[key] = [encode_atom(x) for x in v]
                elif isinstance(v, (int, bytes, str)):
                    udata[key] = encode_atom(v)
                else:
                    raise ValueError("data should be an integer, " "binary, or string, or sequence ")
            data = urlencode(udata, doseq=True)

        del kwargs["auth"]
        event = HttpEvent(method, uri, data)
        if "/messages" in uri.lower() or "/calls" in uri.lower():
            self.events.append(event)
        resp = super().request(method, uri, auth=self.auth, **kwargs)

        event.url = uri
        event.status_code = resp.status_code
        event.response_body = force_text(resp.content)

        return resp
