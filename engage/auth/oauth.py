from django.db import DatabaseError

from engage.utils.class_overrides import MonkeyPatcher

from temba.orgs.models import User as TembaUser

from oauth2_authcodeflow.auth import AuthenticationBackend
from oauth2_authcodeflow.conf import settings

from typing import Dict


class OAuthOverrides(MonkeyPatcher):
    patch_class = AuthenticationBackend

    def get_or_create_user(self, request, id_claims: Dict, access_token: str):
        print("get or create")
        claims = self.get_full_claims(request, id_claims, access_token)
        username = settings.OIDC_DJANGO_USERNAME_FUNC(claims)
        user, created = TembaUser.objects.get_or_create(username=username)
        try:
            self.update_user(user, created, claims, request, access_token)
            user.save()
        except DatabaseError as ex:
            # Saw this happen once, so try to ignore
            if str(ex) != 'Forced update did not affect any rows.':
                raise ex
        return user

    def get_user(self, user_id):
        print("In auth get_user")
        try:
            user = TembaUser.objects.get(pk=user_id)
        except TembaUser.DoesNotExist:  # pragma: no cover
            return None
        return user if self.user_can_authenticate(user) else None
