import pytz
from rest_framework import serializers
from rest_framework.reverse import reverse
from temba.api.v2.views_base import (
    BaseAPIView,
    CreatedOnCursorPagination,
    ListAPIMixin,
)
from temba.channels.models import Channel
from temba.ext.api.models import ExtAPIPermission
from temba.api.models import SSLPermission
from temba.api.v2.serializers import (ReadSerializer)


class ExtChannelReadSerializer(ReadSerializer):
    country = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()
    created_on = serializers.DateTimeField(default_timezone=pytz.UTC)
    last_seen = serializers.DateTimeField(default_timezone=pytz.UTC)

    def get_country(self, obj):
        return str(obj.country) if obj.country else None

    def get_device(self, obj):
        if obj.channel_type != Channel.TYPE_ANDROID:
            return None

        return {
            "name": obj.device,
            "power_level": obj.get_last_power(),
            "power_status": obj.get_last_power_status(),
            "power_source": obj.get_last_power_source(),
            "network_type": obj.get_last_network_type(),
        }

    class Meta:
        model = Channel
        fields = ("uuid", "name", "address", "country", "device", "last_seen", "created_on", "config")


class ExtChannelsEndpoint(ListAPIMixin, BaseAPIView):
    """
    This endpoint allows you to list channels in your account.

    ## Listing All Channels across all organizations.

    A **GET** returns the list of all channels across all organizations, in the order of last created. Note that for
    Android devices, all status information is as of the last time it was seen and can be null before the first sync.

     * **uuid** - the UUID of the channel (string), filterable as `uuid`.
     * **name** - the name of the channel (string).
     * **address** - the address (e.g. phone number, Twitter handle) of the channel (string), filterable as `address`.
     * **country** - which country the sim card for this channel is registered for (string, two letter country code).
     * **device** - information about the device if this is an Android channel:
        * **name** - the name of the device (string).
        * **power_level** - the power level of the device (int).
        * **power_status** - the power status, either ```STATUS_DISCHARGING``` or ```STATUS_CHARGING``` (string).
        * **power_source** - the source of power as reported by Android (string).
        * **network_type** - the type of network the device is connected to as reported by Android (string).
     * **last_seen** - the datetime when this channel was last seen (datetime).
     * **created_on** - the datetime when this channel was created (datetime).

    Example:

        GET /api/v2/channels.json

    Response containing the channels for your organization:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                "name": "Android Phone",
                "address": "+250788123123",
                "country": "RW",
                "device": {
                    "name": "Nexus 5X",
                    "power_level": 99,
                    "power_status": "STATUS_DISCHARGING",
                    "power_source": "BATTERY",
                    "network_type": "WIFI",
                },
                "last_seen": "2016-03-01T05:31:27.456",
                "created_on": "2014-06-23T09:34:12.866",
            }]
        }

    """

    permission_classes = (SSLPermission, ExtAPIPermission)
    permission = "channels.channel_api"
    model = Channel
    serializer_class = ExtChannelReadSerializer
    pagination_class = CreatedOnCursorPagination

    def get_queryset(self):
        return getattr(self.model, self.model_manager).filter()

    def filter_queryset(self, queryset):
        params = self.request.query_params
        queryset = queryset.filter(is_active=True)

        # filter by UUID (optional)
        uuid = params.get("uuid")
        if uuid:
            queryset = queryset.filter(uuid=uuid)

        # filter by address (optional)
        address = params.get("address")
        if address:
            queryset = queryset.filter(address=address)

        c_type = params.get("type")
        if c_type:
            queryset = queryset.filter(channel_type=c_type)

        c_address = params.get("device")
        if c_address:
            queryset = queryset.filter(address=c_address)

        c_mode = params.get("mode")
        if c_mode:
            queryset = queryset.filter(config__contains='"chat_mode": "{}"'.format(c_mode))

        return queryset

    @classmethod
    def get_read_explorer(cls):
        return {
            "method": "GET",
            "title": "List Channels across all Orgs",
            "url": reverse("ext.api.v2.channels"),
            "slug": "channel-list",
            "params": [
                {
                    "name": "uuid",
                    "required": False,
                    "help": "A channel UUID to filter by. ex: 09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                },
                {"name": "address", "required": False, "help": "A channel address to filter by. ex: +250783530001"},
            ],
        }

