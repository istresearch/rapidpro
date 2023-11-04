from django.contrib.auth.models import User as AuthUser, AnonymousUser
from django.utils import timezone
from django.utils.functional import cached_property

from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.logs import LogExtrasMixin

from temba.orgs.models import Org, User as TembaUser

class AnonUserOverrides(MonkeyPatcher):
    """
    Add some stubs so that we avoid 502 errors with certain links if clicked on
    before the user has logged in.
    """
    patch_class = AnonymousUser

    def has_org_perm(self, org, permission: str) -> bool:
        return False
    #enddef has_org_perm

    def is_allowed(self, permission) -> bool:
        return False
    #enddef is_allowed

    def is_any_allowed(self, perm_set: set) -> bool:
        return False
    #enddef is_any_allowed
#endclass AnonUserOverrides

class AuthUserOverrides(MonkeyPatcher):
    patch_class = AuthUser

    # default optional property to False so it exists.
    using_token = False

    def __str__(self):
        return self.name or self.username

    def create(cls: type[AuthUser], email: str, first_name: str, last_name: str, password: str, language: str = None):
        obj = cls.objects.create_user(
            username=email, email=email, first_name=first_name, last_name=last_name, password=password
        )
        if language:
            obj.settings.language = language
            obj.settings.save(update_fields=("language",))
        return obj

    @property
    def name(self) -> str:
        return self.get_full_name()

    @cached_property
    def is_alpha(self) -> bool:
        return self.groups.filter(name="Alpha").exists()

    @cached_property
    def is_beta(self) -> bool:
        return self.groups.filter(name="Beta").exists()

    @cached_property
    def is_support(self) -> bool:
        return self.groups.filter(name="Customer Support").exists()

    @cached_property
    def settings(self):
        assert self.is_authenticated, "can't fetch user settings for anonymous users"
        from temba.orgs.models import UserSettings
        return UserSettings.objects.get_or_create(user=self)[0]

    @cached_property
    def api_token(self) -> str:
        from temba.api.models import get_or_create_api_token

        return get_or_create_api_token(self)

    def as_engine_ref(self) -> dict:
        return {"email": self.email, "name": self.name}

    def record_auth(self):
        """
        Records that this user authenticated
        """
        self.settings.last_auth_on = timezone.now()
        self.settings.save(update_fields=("last_auth_on",))

    def has_org_perm(self, org, permission: str) -> bool:
        """
        Determines if a user has the given permission in the given org.
        """
        if self.is_superuser:
            return True

        if self.is_anonymous:  # pragma: needs cover
            return False

        role = org.get_user_role(self) if org is not None else None
        if not role:
            return False

        return role.has_perm(permission)
    #enddef has_org_perm

    def is_allowed(self, permission) -> bool:
        """
        NOT AVAILABLE ON THE User OBJECT ITSELF!
        Check to see if we have the permission naturally, then if org is
        defined, check there, too.
        :param self: The User object.
        :param permission: A permission to check.
        :return: Returns True if permission is granted.
        """
        if self.has_perm(permission):
            return True
        org = self.get_org() if hasattr(self, 'get_org') and callable(self.get_org) else None
        if org:
            return self.has_org_perm(org, permission)
        return False
    #enddef is_allowed

    def is_any_allowed(self, perm_set: set) -> bool:
        if self.is_superuser:
            return True
        #endif
        if self.is_anonymous:
            return False
        #endif
        org = self.get_org() if hasattr(self, 'get_org') and callable(self.get_org) else None
        return org.is_any_allowed(self, perm_set) if org else False
    #enddef is_any_allowed

    def get_org(self):
        """
        Why do we need this override?: user object may not have its _org prop set.
        Org class has a static method that will either get the org based on the User
        object passed in or via querying the org db.
        :param self: the user object
        :return: the org object as a property of the user obj or from the db.
        """
        if not hasattr(self, "_org") and hasattr(self, "set_org"):
            self.set_org(Org.objects.filter(users=self, is_active=True).first())
        #endif
        return getattr(self, "_org", None)
    #enddef get_org

    def get_orgs(self, *, brands=None, roles=None):
        """
        Why do we need this override?: user orgs not sorted for superadmins.
        :param self: the user object
        :param brands: optional param for branding.
        :param roles: optional param for which roles to check against
        :return: the orgs the user has access to sorted for the org picker.
        """
        #import logging
        #logger = logging.getLogger()
        #logger.debug(f"user={self}", extra={
        #    'roles': roles,
        #})
        if self.is_superuser:
            orgs = Org.objects.all().order_by("name", "slug")
            #import json
            #print(json.dumps(orgs[0]))
            #print(orgs[0].__dict__)
        else:
            orgs = Org.objects.filter(is_active=True).distinct().order_by("name")
            if brands is not None:
                orgs = orgs.filter(brand__in=brands)
            #endif
            if roles is not None:
                orgs = orgs.filter(orgmembership__user=self, orgmembership__role_code__in=[r.code for r in roles])
            else:
                orgs = orgs.filter(orgmembership__user=self)
            #endif
        #endif superuser

        return orgs
    #enddef get_orgs

    def set_org(self, org):
        self._org = org
    #enddef set_org

    def get_owned_orgs(self, *, brand=None):
        """
        Gets the orgs in the given brands where this user is the only user.
        """
        owned_orgs = []
        for org in self.get_orgs(brands=[brand] if brand else None):
            if not org.users.exclude(id=self.id).exists():
                owned_orgs.append(org)
        return owned_orgs

    def set_team(self, team):
        """
        Sets the ticketing team for this user
        """
        self.settings.team = team
        self.settings.save(update_fields=("team",))

#endclass AuthUserOverrides

class TembaUserOverrides(MonkeyPatcher, LogExtrasMixin):
    patch_class = TembaUser

    # default optional property to False so it exists.
    using_token = False

    def is_allowed(self, permission) -> bool:
        """
        NOT AVAILABLE ON THE User OBJECT ITSELF!
        Check to see if we have the permission naturally, then if org is
        defined, check there, too.
        :param self: The User object.
        :param permission: A permission to check.
        :return: Returns True if permission is granted.
        """
        if self.has_perm(permission):
            return True
        org = self.get_org() if hasattr(self, 'get_org') and callable(self.get_org) else None
        if org:
            return self.has_org_perm(org, permission)
        return False
    #enddef is_allowed

    def get_org(self):
        """
        Why do we need this override?: user object may not have its _org prop set.
        Org class has a static method that will either get the org based on the User
        object passed in or via querying the org db.
        :param self: the user object
        :return: the org object as a property of the user obj or from the db.
        """
        if not hasattr(self, "_org"):
            self.set_org(Org.objects.filter(users=self, is_active=True).first())
        #endif
        return getattr(self, "_org", None)
    #enddef get_org

    def get_orgs(self, *, brands=None, roles=None):
        """
        Why do we need this override?: user orgs not sorted for superadmins.
        :param self: the user object
        :param brands: optional param for branding.
        :return: the orgs the user has access to sorted for the org picker.
        """
        if self.is_superuser:
            orgs = Org.objects.all().order_by("name", "slug")
            #import json
            #print(json.dumps(orgs[0]))
            #print(orgs[0].__dict__)
        else:
            orgs = self.orgs.filter(is_active=True).distinct().order_by("name")
            if brands is not None:
                orgs = orgs.filter(brand__in=brands)
            #endif
            if roles is not None:
                orgs = orgs.filter(orgmembership__user=self, orgmembership__role_code__in=[r.code for r in roles])
            #endif
        #endif superuser

        return orgs
    #enddef get_orgs

#endclass TembaUserOverrides
