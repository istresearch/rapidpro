from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from smartmin.views import (
    SmartCRUDL,
    SmartListView,
)

from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES
from temba.channels.models import Channel
from temba.channels.types.postmaster import PostmasterType
from temba.orgs.views import OrgPermsMixin
from temba.utils.views import BulkActionMixin


class Postmaster(SmartCRUDL):
    actions = (
        "list",
    )
    model = Channel
    app_name = 'PM'
    module_name = 'postmaster'
    path = 'pm'

    def permission_for_action(self, action):
        return "%s.%s_%s" % ('channels', self.model_name.lower(), action)
    #enddef permission_for_action
    def template_for_action(self, action):
        return "%s/%s_%s.html" % (self.app_name.lower(), self.module_name.lower(), action)
    #enddef template_for_action
    def url_name_for_action(self, action):
        return "%s.%s_%s" % (self.app_name.lower(), self.module_name.lower(), action)
    #enddef url_name_for_action

    class List(OrgPermsMixin, BulkActionMixin, SmartListView):
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

    #endclass List

#endclass PM
