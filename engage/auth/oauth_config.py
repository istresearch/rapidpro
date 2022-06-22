from getenv import env
import urllib.parse


class OAuthConfig:

    def __init__(self):
        self.OAUTH2_VALIDATOR_CLASS: str = "engage.auth.oauth_validator.EngageOAuth2Validator"
        self.SCOPES: dict = {
            'openid': "OpenID Connect scope",
            'permissions': "permissions",
        }

        self.KEYCLOAK_URL: str = env('KEYCLOAK_URL', None)
        self.KEYCLOAK_REALM: str = env('KEYCLOAK_REALM', 'engage')

        pkey = env('OIDC_RSA_PRIVATE_KEY', None)
        if not pkey:
            pkey64 = env('OIDC_RSA_PRIVATE_KEY_BASE64', None)
            if pkey64:
                import base64
                pkey = base64.b64decode(pkey64)
            #endif base64 rsa key found
        #endif rsa key found
        # see https://django-oauth-toolkit.readthedocs.io/en/latest/oidc.html
        self.OIDC_RSA_PRIVATE_KEY = pkey

        # maybe enabled only if key for it exists?
        self.OIDC_ENABLED: bool = ( self.KEYCLOAK_URL is not None )

        self.KEYCLOAK_CLIENT_ID: str = env('KEYCLOAK_CLIENT_ID', 'engage')
        self.KEYCLOAK_CLIENT_SECRET: str = env('KEYCLOAK_CLIENT_SECRET', 'NOT_A_SECRET')
        self.KEYCLOAK_LOGIN: str = env('KEYCLOAK_LOGIN', None)
        self.REDIRECT_URL: str = env('BRANDING_LOGO_LINK', f"{self.KEYCLOAK_URL}/splash")
    #enddef init

    def is_enabled(self):
        return self.KEYCLOAK_URL is not None
    #enddef is_enabled

    def get_login_redirect(self):
        encodedRedirectUri = urllib.parse.quote(env('TEMBA_HOST'), 'localhost')
        login_url = self.KEYCLOAK_LOGIN
        if not login_url:
            kc_host = self.KEYCLOAK_URL.rstrip('/')
            kc_realm = self.KEYCLOAK_REALM
            login_url = f"{kc_host}/realms/{kc_realm}/protocol/openid-connect/auth"
        #endif
        return login_url + f"?redirect_uri={encodedRedirectUri}"
        #client_id=f{self.KEYCLOAK_CLIENT_ID}
    #enddef get_login_redirect

    def get_logout_redirect(self):
        kc_host = self.KEYCLOAK_URL.rstrip('/')
        kc_realm = self.KEYCLOAK_REALM
        encodedRedirectUri = urllib.parse.quote(self.REDIRECT_URL)
        return f"{kc_host}/realms/{kc_realm}/protocol/openid-connect/logout?redirect_uri={encodedRedirectUri}"
    #enddef get_logout_redirect

#endclass OAuthConfig
#https://auth.dev.istresearch.com/realms/pulse/protocol/openid-connect/auth?redirect_uri=http%3A%2F%2Fengage.dev.local
#https://auth.dev.istresearch.com/realms/pulse/protocol/openid-connect/auth?response_type=code&client_id=pulse-proxy&scope=openid%20profile%20email&state=kwFGvxeNM45p6BWmfXODybfFQN2a11OvoAxxru-7_nY%3D&redirect_uri=https://pulse.dev.istresearch.com/login/oauth2/code/keycloak&nonce=PE2N8leoTiwmUmdFmWHHFmZOw6343jiuMvCNHSE1UDc
