import logging

from engage.utils.class_overrides import MonkeyPatcher

from temba.orgs.views import UserCRUDL
from temba.utils import get_anonymous_user


logger = logging.getLogger()

class OrgViewListUserOverrides(MonkeyPatcher):
    patch_class = UserCRUDL.List

    fields = ("username", "orgs", "date_joined",)
    link_fields = ("username",)
    ordering = ("-date_joined",)
    search_fields = ("username__icontains", "email__icontains",)
    paginate_by = 25
    sort_field = "username"
    non_sort_fields = ('orgs',)
    sort_order = None

    def get_queryset(self: type(UserCRUDL.List), **kwargs):
        """
        override to fix sort order bug: descending uses a leading "-" which fails "if in fields" check.
        """
        queryset = self.super_get_queryset(**kwargs)

        # org users see channels for their org, superuser sees all
        if not self.request.user.is_superuser:
            org = self.request.user.get_org()
            queryset = queryset.filter(org=org)
        #endif

        theOrderByColumn = self.sort_field
        if 'sort_on' in self.request.GET:
            theSortField = self.request.GET.get('sort_on')
            if theSortField in self.fields and theSortField not in self.non_sort_fields:
                self.sort_field = theSortField
                theSortOrder = self.request.GET.get("sort_order")
                self.sort_order = theSortOrder if theSortOrder in ('asc', 'desc') else None
                theSortOrderFlag = '-' if theSortOrder == 'desc' else ''
                theOrderByColumn = "{}{}".format(theSortOrderFlag, self.sort_field)
            #endif
        #endif

        return queryset.filter(is_active=True).order_by(theOrderByColumn, 'username').exclude(id=get_anonymous_user().id)
    #enddef get_queryset

#endclass OrgViewListUserOverrides
