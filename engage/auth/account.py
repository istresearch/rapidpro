"""
Django provides a means to override the default User class, but if you started
you project before such a means was provided, it's really a lot of work to
subclass. RP decided to just continue with the Monkey Patch method of hacking
in methods and properties they want to add to the User class as defined in
temba.orgs.models. Monkey Patching is invisible to our IDEs, however, so to
help developers, this static utilities class was created so we could at least
_FIND_ what kinds of added methods were available. You can then either call
the appropriate method on the User object directly, or you can use these
static methods: e.g. user_obj.get_org() vs UserAcct.get_org(user_obj)
"""


class UserAcct:
    """
    Provide a means to extend the Django User class without replacing it.
    Alternative means to accessing the monkey patches made to User class.
    """
    @staticmethod
    def is_allowed(user, permission) -> bool:
        """
        NOT AVAILABLE ON THE User OBJECT ITSELF!
        Check to see if we have the perimssion naturally, then if org is
        defined, check there, too.
        :param user: The User object.
        :param permission: A permission to check.
        :return: Returns True if permission is granted.
        """
        if user.has_perm(permission):
            return True
        org = user.get_org() if hasattr(user, 'get_org') and callable(user.get_org) else None
        if org:
            return user.has_org_perm(org, permission)
        return False

    #### EVERYTHING BELOW THIS LINE IS A MONKEY PATCH PASSTHRU CALL ============

    @staticmethod
    def release(user, releasing_user, *, brand):
        """
        Releases this user, and any orgs of which they are the sole owner
        """
        return user.release(releasing_user, brand=brand)

    @staticmethod
    def get_org(user):
        return user.get_org()

    @staticmethod
    def set_org(user, org):
        return user.set_org(org)

    @staticmethod
    def is_alpha(user) -> bool:
        return user.is_alpha()

    @staticmethod
    def is_beta(user) -> bool:
        return user.is_beta()

    @staticmethod
    def is_support(user) -> bool:
        return user.is_support()

    @staticmethod
    def get_user_orgs(user, brands=None):
        return user.get_user_orgs(brands)

    @staticmethod
    def get_org_group(user):
        return user.get_org_group()

    @staticmethod
    def get_owned_orgs(user, brand=None):
        """
        Gets all the orgs where this is the only user for the current brand
        """
        return user.get_owned_orgs(brand)

    @staticmethod
    def has_org_perm(user, org, permission) -> bool:
        """
        Determines if a user has the given permission in this org
        """
        return user.has_org_perm(org, permission)

    @staticmethod
    def get_settings(user):
        """
        Gets or creates user settings for this user
        """
        return user.get_settings()

    @staticmethod
    def record_auth(user):
        return user.record_auth()

    @staticmethod
    def enable_2fa(user):
        """
        Enables 2FA for this user
        """
        return user.enable_2fa()

    @staticmethod
    def disable_2fa(user):
        """
        Disables 2FA for this user
        """
        return user.disable_2fa()

    @staticmethod
    def verify_2fa(user, *, otp: str = None, backup_token: str = None) -> bool:
        """
        Verifies a user using a 2FA mechanism (OTP or backup token)
        """
        return user.verify_2fa(otp=otp, backup_token=backup_token)

    @staticmethod
    def as_engine_ref(user) -> dict:
        return user.as_engine_ref()

    @staticmethod
    def name_of(user) -> str:
        return user.name
