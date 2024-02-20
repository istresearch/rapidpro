from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from smartmin.views import SmartListView

from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES
from temba.channels.types.postmaster import PostmasterType
from temba.orgs.views import OrgPermsMixin
from temba.utils.views import BulkActionMixin


class PmViewList(OrgPermsMixin, BulkActionMixin, SmartListView):
    template_name = 'pm/list.html'
    title = "PM Devices"
    fields = ("name", "address", "last_seen",)
    search_fields = ("name", "address", "org__created_by__email",)
    bulk_actions = ("clickme",)

    def get_queryset(self, **kwargs):
        queryset = super().get_queryset(**kwargs)
        org = self.request.user.get_org()
        if not org:
            from engage.utils.middleware import redirect_to
            redirect_to('/')
        #endif
        return queryset.filter(
            is_active=True,
            org=org,
            channel_type=PostmasterType.code,
            schemes='{'+PM_CHANNEL_MODES['PM'].scheme+'}',
        )
    #enddef get_queryset

    def get_name(self, obj):
        return obj.get_name()
    #enddef get_name

    def get_address(self, obj):
        return obj.address if obj.address else _("Unknown")
    #enddef get_address

    def get_gear_links(self):
        links = []
        links.append(
            dict(
                title="Get PM",
                as_btn=True,
                href=reverse("channels.types.postmaster.claim"),
            )
        )
        return links
    #enddef get_gear_links

#endclass PmViewList
