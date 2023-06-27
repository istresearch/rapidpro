import ssl

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.util import ssl_


class TLSAdapter(HTTPAdapter):
    """
    PM repository requires TLS 1.2 and one of the 256 ciphers, requests do not handle that "by default" and we will get
    a ValueError of 'handshake not done yet' without providing our own session adapter and using it where needed.
    @see https://hussainaliakbar.github.io/restricting-tls-version-and-cipher-suites-in-python-requests-and-testing-with-wireshark/
    """
    CIPHERS_ALLOWED: list = (
        'ECDHE-RSA-AES256-GCM-SHA384',
        'ECDHE-ECDSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES256-SHA384',
        'ECDHE-ECDSA-AES256-SHA384',
        'ECDHE-RSA-AES128-GCM-SHA256',
        'ECDHE-RSA-AES128-SHA256:AES256-SHA',
    )
    # a list of a single colon-separated string-list  #facepalm
    ciphers: list = (':'.join(CIPHERS_ALLOWED))

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TLSAdapter, self).__init__(**kwargs)
    #enddef __init__

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(
            ciphers=self.ciphers,
            cert_reqs=ssl.CERT_REQUIRED,
            options=self.ssl_options
        )
        self.poolmanager = PoolManager(
            *pool_args,
            ssl_context=ctx,
            **pool_kwargs
        )
    #enddef init_poolmanager

#endclass TLSAdapter
