import functools
import operator

from temba.orgs.models import Org, OrgRole


def get_user_org(user):
    """
    Why do we need this override?: user object may not have its _org prop set.
    Org class has a static method that will either get the org based on the User
    object passed in or via querying the org db.
    :param user: the user object
    :return: the org object as a property of the user obj or from the db.
    """
    return Org.get_org(user)

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
