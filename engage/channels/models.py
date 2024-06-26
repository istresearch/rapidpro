import json
import logging

import requests
from django.conf import settings

from engage.channels.types.postmaster.postoffice import po_server_url, po_api_key, po_api_header
from engage.utils.class_overrides import MonkeyPatcher

from temba.channels.models import Channel
from temba.contacts.models import URN


class ChannelOverrides(MonkeyPatcher):
    patch_class = Channel

    CONFIG_NAME_FORMAT = "name_format"
    CONFIG_PHONE_NUMBER = "phone_number"
    CONFIG_DEVICE_MODEL = "device_model"
    CONFIG_IMEI = "imei"

    def create(
            cls: type[Channel],
            org,
            user,
            country,
            channel_type,
            name=None,
            address=None,
            config=None,
            role=Channel.DEFAULT_ROLE,
            tps=10,
            schemes=None,
            **kwargs,
    ):
        if config is None:
            config = {}
        #endif
        # P4-3462
        if schemes and URN.TEL_SCHEME in schemes:
            config[Channel.CONFIG_ALLOW_INTERNATIONAL] = True
        #endif

        tps = getattr(settings, "DEFAULT_TPS", tps)

        return cls.Channel_create(org=org, user=user, country=country, channel_type=channel_type,
                name=name, address=address, config=config, role=role, schemes=schemes, tps=tps, **kwargs
        )
    #enddef create

    def claim(self, org, user, phone):
        # NOTE: leaving alert_email field empty, which is the user.email param.
        user.email = None
        return self.Channel_claim(org=org, user=user, phone=phone)
    #enddef claim

    def release(self: Channel, user, *, trigger_sync: bool = True, check_dependent_flows: bool = True):
        if check_dependent_flows:
            dependent_flows_count = self.dependent_flows.count()
            if dependent_flows_count > 0:
                raise ValueError(f"Cannot delete Channel: {self.get_name()}, used by {dependent_flows_count} flows")
            #endif
        #endif
        return self.Channel_release(user, trigger_sync=trigger_sync)
    #enddef release

    @property
    def apps(self: Channel):
        return self.config['apps'] if 'apps' in self.config else ''
    #enddef apps

    @property
    def device_id(self: Channel):
        return self.address
    #enddef device_id

    @property
    def name_format(self: Channel):
        return self.config[self.CONFIG_NAME_FORMAT] if self.CONFIG_NAME_FORMAT in self.config else ''
    #enddef name_format

    @property
    def pm_scheme(self: Channel):
        return self.schemes[0].strip('{}')
    #enddef pm_scheme

    @property
    def children(self: Channel):
        ''' keeping around as example RawSQL, chat_mode is not used anymore
        from django.db.models.expressions import RawSQL
        return Channel.objects.annotate(
            my_chat_mode=RawSQL("config::json->>'chat_mode'", [])
        ).filter(parent=self, is_active=True).order_by('my_chat_mode')
        '''
        return Channel.objects.filter(parent=self, is_active=True).order_by('schemes')
    #enddef children

    @staticmethod
    def call_po_server(endpoint: str, data: dict, user):
        if po_server_url is not None and po_api_key is not None:
            logger = logging.getLogger()
            r = requests.post(
                f"{po_server_url}/engage{endpoint}",
                headers={
                    po_api_header: str(po_api_key),
                    "po-api-client-id": str(user.id),
                },
                json=data,
                cookies=None,
                verify=False,
                timeout=10,
            )
            if r.status_code == 200:
                return json.loads(r.content)["data"]
            else:
                logger.error("po api failure", extra={
                    'status_code': r.status_code,
                    'resp': r,
                })
            #endif
        #endif
    #enddef call_po_server

    @staticmethod
    def fetch_claim_qr(org, user, name_format):
        data = {
            'org_id': org.id,
            'org_name': org.name,
            'created_by': user.id,
            'name_format': name_format,
        }
        return Channel.call_po_server('/claim', data, user)
    #enddef fetch_claim_qr

    @staticmethod
    def fetch_device_info(user, device_id):
        data = {
            'device_ids': [device_id],
        }
        respData = Channel.call_po_server('/device/info', data, user)
        if respData and 'devices' in respData and len(respData['devices']) > 0:
            return respData['devices'][0]
        #endif
    #enddef fetch_qr_code

    @staticmethod
    def formatChannelName(name_format, channel: Channel, user):
        user_name = user.first_name or user.last_name or user.username
        phone_num = channel.address
        if name_format and (name_format.find('{{phone_number}}') >= 0 or name_format.find('{{device_model}}')):
            # call po api for device metadata
            device_info = Channel.fetch_device_info(user, channel.address)
            if device_info and device_info['meta']:
                if device_info['meta']['phone_num']:
                    phone_num: str = device_info['meta']['phone_num']
                    if not phone_num.startswith('+'):
                        phone_num = '+' + phone_num
                    #endif
                #endif
                device_model = device_info['meta']['device_model']
            #endif
        #endif
        channel_name = (
            name_format
            .replace('{{device_id}}', channel.address)
            .replace('{{pm_scheme}}', channel.pm_scheme)
            .replace('{{pm_mode}}', channel.pm_scheme)
            .replace('{{phone_number}}', phone_num)
            .replace('{{device_model}}', device_model)
            .replace('{{org}}', user.get_org().name)
            .replace('{{first_name}}', user_name)
        )
        return channel_name
    #enddef formatChannelName

#endclass ChannelOverrides


from temba.channels.types.android.type import AndroidType
class AndroidTypeOverrides(MonkeyPatcher):
    patch_class = AndroidType
    # existing channels won't crash the system, but cannot add new channels of this type.
    beta_only = True
#endclass
