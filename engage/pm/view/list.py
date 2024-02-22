from django.shortcuts import redirect
from django.urls import reverse

from smartmin.views import SmartListView

from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES
from temba.channels.types.postmaster import PostmasterType
from temba.orgs.views import OrgPermsMixin
from temba.utils.views import BulkActionMixin


class PmViewList(OrgPermsMixin, BulkActionMixin, SmartListView):
    template_name = 'pm/list.html'
    title = "PM Devices"
    fields = ("device_name", "address", "uuid", "last_seen",)
    field_config = {"address": {"label": "Device ID"}, "uuid": {"label": "UUID"}}
    search_fields = ("name", "address", "config__icontains", "uuid", "last_seen__icontains",)
    bulk_actions = ("clickme",)
    secondary_order_by = ["name"]
    default_order = ("-last_seen",)
    non_sort_fields = ()
    link_url = 'uuid@pm.postmaster_read'

    def get_queryset(self, **kwargs):
        org = self.request.user.get_org()
        if not org:
            from engage.utils.middleware import redirect_to
            redirect_to('/')
        #endif
        queryset = super().get_queryset(**kwargs)
        queryset = queryset.filter(
            is_active=True,
            org=org,
            channel_type=PostmasterType.code,
            schemes='{'+PM_CHANNEL_MODES['PM'].scheme+'}',
        )
        #search_query = self.request.GET.get("search", None)
        sort_on = self.request.GET.get("sort_on", None)
        if sort_on:
            self.sort_direction = "desc" if sort_on.startswith("-") else "asc"
            self.sort_field = sort_on.lstrip("-")
            sort_order = [sort_on]
        else:
            self.sort_direction = None
            self.sort_field = None
            sort_order = []
        #endif
        sort_order += self.secondary_order_by
        queryset.order_by(*sort_order).prefetch_related("org")
        return queryset
    #enddef get_queryset

    def render_to_response(self, context, **response_kwargs):
        search_sesskey = 'pm.postmaster.search'
        arg_search = self.request.GET.get('search', None)
        if arg_search is None and self.request.session.get(search_sesskey, None):
            return redirect(f"{reverse('pm.postmaster_list')}?search={self.request.session[search_sesskey]}")
        elif arg_search != '':
            self.request.session[search_sesskey] = arg_search
        else:
            if self.request.session.get(search_sesskey, None):
                del self.request.session[search_sesskey]
            # remove the "?search=" for empty string as it messes up pagination
            return redirect(f"{reverse('pm.postmaster_list')}")
        #endif search is part of request
        return super().render_to_response(context, **response_kwargs)
    #enddef render_to_response

    def get_gear_links(self):
        links = []
        links.append(
            dict(
                title="Add PM",
                as_btn=True,
                href=reverse("channels.types.postmaster.claim"),
            )
        )
        return links
    #enddef get_gear_links

#endclass PmViewList
