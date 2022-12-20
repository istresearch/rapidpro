import functools
import operator

from django.db import transaction

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.orgs.models import Org, OrgRole
import temba.settings as siteconfig


def get_user_org(user):
    """
    Why do we need this override?: user object may not have its _org prop set.
    Org class has a static method that will either get the org based on the User
    object passed in or via querying the org db.
    :param user: the user object
    :return: the org object as a property of the user obj or from the db.
    """
    return Org.get_org(user)
#enddef get_user_org


def get_user_orgs(user, brands=None):
    """
    Why do we need this override?: user orgs not sorted for superadmins.
    :param user: the user object
    :param brands: optional param for branding.
    :return: the orgs the user has access to sorted for the org picker.
    """
    if user.is_superuser:
        theList = Org.objects.all().order_by("name", "slug")
        #import json
        #print(json.dumps(theList[0]))
        #print(theList[0].__dict__)
        return theList

    org_sets = [role.get_orgs(user) for role in OrgRole]
    user_orgs = functools.reduce(operator.or_, org_sets)

    if brands:
        user_orgs = user_orgs.filter(brand__in=brands)

    return user_orgs.filter(is_active=True).distinct().order_by("name")
#enddef get_user_orgs


class OrgModelOverride(ClassOverrideMixinMustBeFirst, Org):
    override_ignore = ignoreDjangoModelAttrs(Org)

    # we do not want Django to perform any magic inheritance
    class Meta:
        abstract = True

    def get_brand_domain(self):
        if siteconfig.ALT_CALLBACK_DOMAIN:
            return siteconfig.ALT_CALLBACK_DOMAIN
        else:
            return self.getOrigClsAttr('get_brand_domain')(self)
    #enddef get_brand_domain

    def release(self, user, **kwargs):
        with transaction.atomic():
            self.getOrigClsAttr('release')(self, user, **kwargs)
        #endwith
    #enddef release

#endclass OrgModelOverride
