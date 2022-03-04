from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from smartmin.views import SmartListView
from temba import settings
from temba.channels.models import SyncEvent
from temba.orgs.views import OrgPermsMixin


class ManageChannelMixin:

    class Manage(OrgPermsMixin, SmartListView):
        paginate_by = settings.PAGINATE_CHANNELS_COUNT
        title = _("Manage Channels")
        permission = "channels.channel_claim"
        sort_field = "created_on"
        link_url = 'uuid@channels.channel_read'
        link_fields = ("name", "uuid", "address", "channel_log", "settings")
        field_config = {"channel_type": {"label": "Type"}, "uuid": {"label": "UUID"}}
        fields = (
            'name', 'channel_type', 'last_seen', 'uuid', 'address', 'country', 'device', 'channel_log', 'settings',
        )
        search_fields = (
            "name__icontains", "channel_type__icontains", "last_seen__icontains", "uuid__icontains",
            "address__icontains", "country__icontains", "device__icontains",
        )
        non_sort_fields = ('channel_log', 'settings')
        sort_order = None

        def get_gear_links(self):
            links = []

            links.append(dict(title=_("Logout"), style="hidden", href=reverse("users.user_logout")))

            if self.has_org_perm("channels.channel_claim"):
                links.append(dict(title=_("Add Channel"), href=reverse("channels.channel_claim")))

            return links

        def get_channel_log(self, obj):
            return "Channel Log"

        def get_settings(self, obj):
            return "Settings"

        def lookup_field_link(self, context, field, obj):
            if field == 'channel_log':
                return reverse('channels.channellog_list', args=[obj.uuid])
            elif field == 'settings':
                return reverse("channels.channel_configuration", args=[obj.uuid])
            else:
                return reverse('channels.channel_read', args=[obj.uuid])

        def has_org_perm(self, permission):
            if self.org:
                return self.get_user().has_org_perm(self.org, permission)
            return False

        def get_queryset(self, **kwargs):
            """
            override to fix sort order bug (descending uses a leading "-" which fails "if in fields" check.
            """
            queryset = super().get_queryset(**kwargs)

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

            return queryset.filter(is_active=True).order_by(theOrderByColumn, 'name', 'address', 'uuid').prefetch_related("sync_events")

        def get_queryset_orig(self, **kwargs):
            queryset = super().get_queryset(**kwargs)

            # org users see channels for their org, superuser sees all
            if not self.request.user.is_superuser:
                org = self.request.user.get_org()
                queryset = queryset.filter(org=org)

            if 'sort_on' in self.request.GET:
                if self.request.GET['sort_on'] in self.fields:
                    self.sort_field = self.request.GET['sort_on']

            return queryset.filter(is_active=True).order_by(self.sort_field).prefetch_related("sync_events")

        def pre_process(self, *args, **kwargs):
            # superuser sees things as they are
            if self.request.user.is_superuser:
                return super().pre_process(*args, **kwargs)

            return super().pre_process(*args, **kwargs)

        def get_name(self, obj):
            return obj.get_name()

        def get_address(self, obj):
            return obj.address if obj.address else _("Unknown")

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            # delayed sync event
            sync_events = SyncEvent.objects.filter(channel__in=context['channel_list']).order_by("-created_on")
            for channel in context['channel_list']:
                if not (channel.created_on > timezone.now() - timedelta(hours=1)):
                    if sync_events:
                        for sync_event in sync_events:
                            if sync_event.channel_id == channel.id:
                                latest_sync_event = sync_events[0]
                                interval = timezone.now() - latest_sync_event.created_on
                                seconds = interval.seconds + interval.days * 24 * 3600
                                channel.last_sync = latest_sync_event
                                if seconds > 3600:
                                    channel.delayed_sync_event = latest_sync_event
            context['sort_field'] = self.sort_field
            return context
