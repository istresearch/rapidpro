from oauth2_provider.oauth2_validators import OAuth2Validator


class EngageOAuth2Validator(OAuth2Validator):

    def get_additional_claims(self):
        return {
            "given_name": lambda request: request.user.first_name,
            "family_name": lambda request: request.user.last_name,
            "name": lambda request: ' '.join([request.user.first_name, request.user.last_name]),
            "preferred_username": lambda request: request.user.username,
            "email": lambda request: request.user.email,
            "permissions": lambda request: list(request.user.get_group_permissions()),
        }
