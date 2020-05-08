import pytz
from rest_framework import serializers, status
from rest_framework.reverse import reverse

from temba.api.support import InvalidQueryError
from temba.api.v2.views_base import (
    BaseAPIView,
    CreatedOnCursorPagination,
    ListAPIMixin,
    DeleteAPIMixin, WriteAPIMixin)
from rest_framework.response import Response
from temba.channels.models import Channel
from temba.ext.api.models import ExtAPIPermission
from temba.api.models import SSLPermission
from temba.api.v2.serializers import (ReadSerializer, WriteSerializer)
from temba.orgs.models import Org
import json

class ExtChannelReadSerializer(ReadSerializer):
    country = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()
    created_on = serializers.DateTimeField(default_timezone=pytz.UTC)
    last_seen = serializers.DateTimeField(default_timezone=pytz.UTC)
    config = serializers.SerializerMethodField()

    def get_country(self, obj):
        return str(obj.country) if hasattr(obj, 'country') else None

    def get_config(self, obj):
        if not hasattr(obj, 'config'):
            return None

        return obj.config


    def get_device(self, obj):
        if hasattr(obj, 'channel_type') and obj.channel_type != Channel.TYPE_ANDROID:
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


class ExtChannelWriteSerializer(WriteSerializer):

    def validate_unit(self, value):
        return self.UNITS[value]

    def validate(self, data):
        return data

    def save(self):
        params = self.context['request'].query_params
        channel_type = params.get("type")
        if not channel_type:
            raise InvalidQueryError(
                "URL must contain a type parameter. ex: /ext/api/v2/channels.json?type=PSM&param1=val1&paramN=valN"
            )

        data = {}
        for p in params:
            if p == 'org':
                org = Org.objects.filter(id=params[p]).first()
                if org is not None:
                    self.context['request'].user.set_org(org)
            else:
                data[p] = params[p]
        type_from_code = Channel.get_type_from_code(channel_type)
        type_from_code.claim_view.request = self.context['request']
        form = type_from_code.claim_view.Form(data=data, request=self.context['request'], channel_type=channel_type)
        is_valid = form.is_valid()
        if not is_valid:
            ret = Channel(uuid=None, name=None, address=None, country=None, device=None,
                          last_seen=None, created_on=None, config=form.errors.as_json())
            return ret
        ret = type_from_code.claim_view(channel_type).form_valid(form)
        return Channel.objects.filter(uuid=ret.url.split("/")[len(ret.url.split("/"))-2]).first()


class ExtChannelsEndpoint(ListAPIMixin, WriteAPIMixin, DeleteAPIMixin, BaseAPIView):
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
     * **config** - the channels config OR errors if the channel creation fails.

    Example:

        GET /ext/api/v2/channels.json

    Response containing the channels for your organization:

        {
            "next": null,
            "previous": null,
            "results": [
            {
                "uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                "name": "Android Phone",
                "address": "pm_whatsapp_1",
                "country": "RW",
                "config": {
                    "device_id": "TgPM",
                    "chat_mode": "TG",
                    "callback_domain": "83f83d51.ngrok.io",
                    "org_id": "1",
                },
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

    ## Adding a Channel

    A **POST** can be used to create a new channel.

    * **type** - the channel type (string)
    * **params[]** - A list of parameter name/value mappings that are acceptable to the target channel type, as defined
    in the channels claim view Form.

    Example:

        POST /ext/api/v2/channels.json?type=PSM&chat_mode=WA&device_id=weezer

    You will receive a Channel object as a response if successful:

        {
            "uuid":"ef62ca26-023e-4c88-a939-0945e711e979",
            "name":"weezer",
            "address":"weezer",
            "country":"",
            "device":null,
            "last_seen":"2020-03-30T16:29:13.078071Z",
            "created_on":"2020-03-30T16:29:13.077260Z",
            "config": {
                "device_id": "weezer",
                "chat_mode": "WA",
                "callback_domain": "83f83d51.ngrok.io",
                "org_id": 2
            }
        }
    """

    permission_classes = (SSLPermission, ExtAPIPermission)
    permission = "channels.channel_api"
    model = Channel
    serializer_class = ExtChannelReadSerializer
    write_serializer_class = ExtChannelWriteSerializer
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

        claim_code = params.get("claim_code")
        if claim_code:
            queryset = queryset.filter(config__contains='"claim_code": "{}"'.format(claim_code))

        c_type = params.get("type")
        if c_type:
            queryset = queryset.filter(channel_type=c_type)

        c_address = params.get("device_id")
        if c_address:
            queryset = queryset.filter(address=c_address)

        c_mode = params.get("mode")
        if c_mode:
            queryset = queryset.filter(config__contains='"chat_mode": "{}"'.format(c_mode))

        return queryset

    def delete(self, request, *args, **kwargs):
        self.lookup_values = self.get_lookup_values()

        if not self.lookup_values:
            raise InvalidQueryError(
                "URL must contain one of the following parameters: " + ", ".join(sorted(self.lookup_params.keys()))
            )

        channel = self.get_object()
        if channel is not None:
            data = {
                "name": channel.device,
                "id": channel.id,
                "uuid": channel.uuid,
                "is_active": channel.is_active,
                "response": {
                    "status": status.HTTP_200_OK,    # Default to STATUS 200 OK
                    "errors": [],
                    "dependent_flows": [],
                },
            }
            try:
                channel.release()
            except Exception as e:
                data["response"]["status"] = status.HTTP_400_BAD_REQUEST
                data["response"]["errors"] = e.args
                dependent_flows = []
                for flow in channel.dependent_flows.distinct():
                    dependent_flows.append(flow)
                data["response"]["dependent_flows"] = dependent_flows
            return Response(content_type="application/json", data=data, status=data["response"]["status"])

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
                {"device_id": "device id", "required": False, "help": "A postmaster Device ID  to filter by. ex: pm_whatsapp_1"},
                {"mode": "chat mode", "required": False, "help": "A Postmaster chat mode to filter by. ex WA, TG, SMS"},
            ],
        }

    @classmethod
    def get_write_explorer(cls):
        return {
            "method": "POST",
            "title": "Create Channel",
            "url": reverse("ext.api.v2.channels"),
            "slug": "channel-write",
            "fields": [
                {"name": "type", "required": True, "help": "The type of channel you want to create"},
                {"name": "org", "required": True, "help": "The Org that the channel will be created in"},
                {"name": "params[]", "required": True, "help": "A list of parameter name/value mappings that are "
                                                               "acceptable to the target channel type, as defined "
                                                               "in the channels claim view Form."},
            ],
        }

    @classmethod
    def get_delete_explorer(cls):
        return {
            "method": "DELETE",
            "title": "Delete Channel",
            "url": reverse("ext.api.v2.channels"),
            "slug": "channel-delete",
            "fields": [
                {"name": "uuid", "required": True, "help": "The uuid of the channel to be deleted"},
            ],
        }