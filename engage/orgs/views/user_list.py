import logging

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.orgs.views import UserCRUDL
from temba.utils import get_anonymous_user


logger = logging.getLogger(__name__)

class OrgViewListUserOverrides(ClassOverrideMixinMustBeFirst, UserCRUDL.List):
    fields = ("username", "orgs", "date_joined",)
    link_fields = ("username",)
    ordering = ("-date_joined",)
    search_fields = ("username__icontains", "email__icontains",)
    paginate_by = 25
    sort_field = "username"
    non_sort_fields = ('orgs',)
    sort_order = None

    @staticmethod
    def on_apply_overrides(under_cls) -> None:
        ClassOverrideMixinMustBeFirst.setOrigMethod(under_cls, 'get_queryset')
    #enddef on_apply_overrides

    def get_queryset(self, **kwargs):
        """
        override to fix sort order bug (descending uses a leading "-" which fails "if in fields" check.
        """
        queryset = self.orig_get_queryset(**kwargs)

        # org users see channels for their org, superuser sees all
        if not self.request.user.is_superuser:
            org = self.request.user.get_org()
            queryset = queryset.filter(org=org)

        theOrderByColumn = self.sort_field
        if 'sort_on' in self.request.GET:
            theSortField = self.request.GET.get('sort_on')
            if theSortField in self.fields and theSortField not in self.non_sort_fields:
                self.sort_field = theSortField
                theSortOrder = self.request.GET.get("sort_order")
                self.sort_order = theSortOrder if theSortOrder in ('asc', 'desc') else None
                theSortOrderFlag = '-' if theSortOrder == 'desc' else ''
                theOrderByColumn = "{}{}".format(theSortOrderFlag, self.sort_field)

        return queryset.filter(is_active=True).order_by(theOrderByColumn, 'name').exclude(id=get_anonymous_user().id)


#endclass OrgViewListUserOverrides
