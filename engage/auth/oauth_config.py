from getenv import env
from pathlib import Path
import urllib.parse

from engage.utils.strings import str2bool

class OAuthConfig:
    """
    Class housing our SSO ODIC configuration as well as helper methods and notes.
    Plugin used: https://github.com/jrd/django-oauth2-authcodeflow
    NOTES:
        constants to be aware of from plugin:
        OIDC_URL_AUTHENTICATION_NAME = 'oidc_authentication'
        OIDC_URL_CALLBACK_NAME = 'oidc_callback'  #the 'redirect_url' keyguard needs
        OIDC_URL_LOGOUT_NAME = 'oidc_logout'
        OIDC_URL_TOTAL_LOGOUT_NAME = 'oidc_total_logout'
        OIDC_URL_LOGOUT_BY_OP_NAME = 'oidc_logout_by_op'  #the 'logout_url' keyguard needs
        OIDC_FROM_CLI_QUERY_STRING = 'from_cli'
    """

    def __init__(self):
        self.OAUTH2_VALIDATOR_CLASS: str = "engage.auth.oauth_validator.EngageOAuth2Validator"
        self.SCOPES: dict = {
            'openid': "OpenID Connect scope",
            'email': "Email",
            'profile': "Profile",
            'roles': "Roles",
            #'offline_access': "Get Refresh Token",
        }

        self.KEYCLOAK_URL: str = env('KEYCLOAK_URL', None)
        if self.KEYCLOAK_URL is not None and not self.KEYCLOAK_URL.endswith('/'):
            self.KEYCLOAK_URL += '/'
        #endif
        self.KEYCLOAK_REALM: str = env('KEYCLOAK_REALM', 'engage')

        # RSA KEY IS OPTIONAL, but recommended for stronger security
        # see https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html#creating-rsa-private-key
        self.OIDC_RSA_PRIVATE_KEY = env('OIDC_RSA_PRIVATE_KEY', None)
        if not self.OIDC_RSA_PRIVATE_KEY:
            pkey64 = env('OIDC_RSA_PRIVATE_KEY_BASE64', None)
            if pkey64:
                import base64
                self.OIDC_RSA_PRIVATE_KEY = base64.b64decode(pkey64)
            else:
                pkeyfile = env('OIDC_RSA_PRIVATE_KEY_FILE', None)
                if len(pkeyfile) > 1:
                    pkeypath = Path(pkeyfile)
                    if pkeypath.is_file():
                        self.OIDC_RSA_PRIVATE_KEY = pkeypath.read_text()
                    #endif is existing file
                #endif filepath env var non-empty
            #endif base64 rsa key found
        #endif rsa key found

        # maybe enabled only if key for it exists?
        self.OIDC_ENABLED: bool = ( self.KEYCLOAK_URL is not None and len(self.KEYCLOAK_URL) > 1 )

        self.KEYCLOAK_CLIENT_ID: str = env('KEYCLOAK_CLIENT_ID', 'engage')
        self.KEYCLOAK_CLIENT_SECRET: str = env('KEYCLOAK_CLIENT_SECRET', 'NOT_A_SECRET')
        self.KEYCLOAK_LOGIN: str = env('KEYCLOAK_LOGIN', None)
        self.KEYCLOAK_REPLACES_LOGIN: bool = str2bool(env('KEYCLOAK_REPLACES_LOGIN', False))
        self.REDIRECT_URL: str = env('BRANDING_LOGO_LINK', f"{self.KEYCLOAK_URL}splash")

        self.is_enabled = self.OIDC_ENABLED
        self.is_login_replaced = self.KEYCLOAK_REPLACES_LOGIN
        self.sso_login_url = self.KEYCLOAK_LOGIN
    #enddef init

    def get_discovery_url(self):
        return f"{self.KEYCLOAK_URL}.well-known/openid-configuration"
    #enddef get_discovery_url

    def get_login_redirect(self):
        encodedRedirectUri = urllib.parse.quote(env('TEMBA_HOST'), 'localhost')
        return encodedRedirectUri
    #enddef get_login_redirect

    def get_login_url(self):
        return f"/oidc/authenticate?next={self.get_login_redirect()}"
        # login_url = self.KEYCLOAK_LOGIN
        # if not login_url:
        #     kc_host = self.KEYCLOAK_URL
        #     kc_realm = self.KEYCLOAK_REALM
        #     login_url = f"{kc_host}realms/{kc_realm}/protocol/openid-connect/auth"
        # #endif
        # return login_url + f"?redirect_uri={self.get_login_redirect()}"
    #enddef get_login_url

    def get_logout_redirect(self):
        encodedRedirectUri = urllib.parse.quote(self.REDIRECT_URL)
        return encodedRedirectUri
    #enddef get_logout_redirect

    def get_logout_url(self):
        return f"/oidc/total_logout?next={self.get_login_redirect()}"
        # kc_host = self.KEYCLOAK_URL
        # kc_realm = self.KEYCLOAK_REALM
        # encodedRedirectUri = urllib.parse.quote(self.REDIRECT_URL)
        # return f"{kc_host}realms/{kc_realm}/protocol/openid-connect/logout?redirect_uri={self.get_logout_redirect()}"
    #enddef get_logout_redirect

#endclass OAuthConfig
