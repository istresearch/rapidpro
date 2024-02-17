from django.utils.translation import gettext_lazy as _

from smartmin.views import (
    SmartCRUDL,
    SmartListView,
)

from temba.channels.models import Channel
from temba.orgs.views import OrgPermsMixin


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

    class List(OrgPermsMixin, SmartListView):
        template_name = 'pm/list.html'
        title = "PM Devices"
        fields = ("name", "address", "last_seen")
        search_fields = ("name", "address", "org__created_by__email")

        def get_queryset(self, **kwargs):
            queryset = super().get_queryset(**kwargs)

            # org users see channels for their org, superuser sees all
            if not self.request.user.is_superuser:
                org = self.request.user.get_org()
                queryset = queryset.filter(org=org)

            return queryset.filter(is_active=True)
        #enddef get_queryset

        def get_name(self, obj):
            return obj.get_name()
        #enddef get_name

        def get_address(self, obj):
            return obj.address if obj.address else _("Unknown")
        #enddef get_address

    #endclass List

#endclass PM
