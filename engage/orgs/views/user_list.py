import logging

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.orgs.views import UserCRUDL


logger = logging.getLogger(__name__)

class OrgViewListUserMixin(ClassOverrideMixinMustBeFirst, UserCRUDL.List):
    fields = ("username", "orgs", "date_joined")
    link_fields = ("username",)
    ordering = ("-date_joined",)
    search_fields = ("username__icontains", "email__icontains")
    paginate_by = 25


#endclass OrgViewListUserMixin
