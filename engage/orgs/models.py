import functools
import operator

from temba.orgs.models import Org, OrgRole

def get_user_orgs(user, brands=None):
    if user.is_superuser:
        # override temba so poor admin has name sorted orgs
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
