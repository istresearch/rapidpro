from django.db.models import Sum
from django.urls import reverse

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst
from engage.utils.logs import LogExtrasMixin
from engage.utils.strings import str2bool

from temba.orgs.views import OrgCRUDL


class AdminManageOverrides(ClassOverrideMixinMustBeFirst, LogExtrasMixin, OrgCRUDL.Manage):
    title = "Workspaces"
    default_order = 'name'

    def get_gear_links(self) -> list:
        links = [
            dict(
                id='btn-create-workspace',
                title='New Workspace',
                style='button-primary',
                href=reverse("orgs.org_create"),
                as_btn=True,
            ), dict(
                id='btn-grant-workspace',
                title='Grant',
                style='button-primary',
                href=reverse("orgs.org_grant"),
            ),
        ]
        return links
    #enddef get_gear_links

    def derive_queryset(self, **kwargs):
        queryset = super(OrgCRUDL.Manage, self).derive_queryset(**kwargs)
        bActiveFilter = not self.request.GET.get("inactive")
        queryset = queryset.filter(is_active=bActiveFilter)

        brands = self.request.branding.get("keys")
        if brands:
            queryset = queryset.filter(brand__in=brands)

        anon = self.request.GET.get("anon")
        if anon:
            queryset = queryset.filter(is_anon=str2bool(anon))

        suspended = self.request.GET.get("suspended")
        if suspended:
            queryset = queryset.filter(is_suspended=str2bool(suspended))

        flagged = self.request.GET.get("flagged")
        if flagged:
            queryset = queryset.filter(is_flagged=str2bool(flagged))

        queryset = queryset.annotate(credits=Sum("topups__credits"))
        queryset = queryset.annotate(paid=Sum("topups__price"))

        return queryset
    #enddef derive_queryset

    def get_context_data(self, **kwargs):
        context = super(OrgCRUDL.Manage, self).get_context_data(**kwargs)
        context["searches"] = []
        context["anon_query"] = str2bool(self.request.GET.get("anon"))
        context["flagged_query"] = str2bool(self.request.GET.get("flagged"))
        context["suspended_query"] = str2bool(self.request.GET.get("suspended"))
        return context
    #enddef get_context_data

#endclass AdminManageMixin
