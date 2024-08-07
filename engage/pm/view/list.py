import json

import requests
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import force_str

from smartmin.views import SmartListView
from rest_framework import status

from engage.channels.purge_outbox import PurgeOutboxMixin
from engage.channels.types.postmaster.postoffice import po_api_key
from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES
from temba.channels.types.postmaster import PostmasterType
from temba.orgs.views import OrgPermsMixin
from temba.utils.views import BulkActionMixin

from engage.channels.types.postmaster.postoffice import (
    po_server_url,
    po_api_key,
    po_api_header,
)


class PmViewList(PurgeOutboxMixin, OrgPermsMixin, BulkActionMixin, SmartListView):
    template_name = 'pm/list.html'
    title = "PM Devices"
    fields = ("name", "address", "children", "last_seen",)
    field_config = {
        "address": {"label": "Device ID"},
        "uuid": {"label": "UUID"},
        "children": {"label": "APPS"},
    }
    search_fields = ("name__icontains", "address__icontains", "uuid__icontains", "last_seen__icontains",)
    secondary_order_by = ["name"]
    default_order = ("-last_seen",)
    non_sort_fields = ('children',)
    link_url = 'uuid@pm.postmaster_read'

    def get_bulk_actions(self):
        bulk_actions = ()
        if self.has_org_perm(PurgeOutboxMixin.PurgeOutbox.permission):
            bulk_actions += PurgeOutboxMixin.get_actions()
        #endif
        if self.has_org_perm("channels.channel_update"):
            bulk_actions += ('rename',)
        #endif
        return bulk_actions
    #enddef get_bulk_actions

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
        sort_on = self.request.GET.get("_order", None)
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
        queryset.order_by(*sort_order)
        queryset.prefetch_related("org")
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
        if self.has_org_perm('channels.channel_create'):
            links.append(
                dict(
                    title="Add PM",
                    as_btn=True,
                    href=reverse("channels.types.postmaster.claim"),
                )
            )
        #endif

        return links
    #enddef get_gear_links

    @staticmethod
    def get_commands_list():
        if po_server_url is not None and po_api_key is not None:
            r = requests.get(
                f"{po_server_url}/engage/commands/list",
                headers={po_api_header: po_api_key},
                cookies=None,
                verify=False,
            )
            if r.status_code == status.HTTP_200_OK:
                return json.loads(r.content)["data"]
            #endif
        return None
    #enddef get_commands_list

    @staticmethod
    def post_commands(data):
        if po_server_url is not None and po_api_key is not None:
            response = requests.post(
                f"{po_server_url}/engage/commands/send",
                headers={po_api_header: po_api_key},
                json=data,
                cookies=None,
                verify=False,
            )
            return JsonResponse(response.json(), status=response.status_code)
            #endif
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
    #enddef post_commands

    def post(self, request, *args, **kw1args):
        data = json.loads(force_str(request.body))
        user = self.request.user
        org = user.get_org()
        data["user_id"] = user.id
        data["org_id"] = org.id

        return self.post_commands(data)
    #enddef post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        commands = self.get_commands_list()
        context['commands_list'] = json.dumps(commands)

        return context
    #enddef get_context_data

#endclass PmViewList
