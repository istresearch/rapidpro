from copy import deepcopy
from typing import Union, Any
from uuid import uuid4

from django.db import migrations
from django.db.models import Q

from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES
from temba.channels.types.postmaster import PostmasterType


parent_chat_mode = 'PM'
parent_scheme: str = PM_CHANNEL_MODES[parent_chat_mode].scheme
parent_schemes: str = '{'+parent_scheme+'}'

UPDATE_EXISTING_PM_SERVICE_CHANNELS_AS_PARENT_SQL = """
UPDATE channels_channel ch
   SET parent_id=par.id FROM channels_channel par
 WHERE par.address=ch.address
   AND par.is_active=ch.is_active
   AND par.channel_type = '%(pm_code)s'
   AND par.schemes = '%(pm_schemes)s'
   AND ch.channel_type = par.channel_type
   AND ch.schemes != par.schemes
   AND ch.is_active=True
   AND ch.parent_id is null
""" % {
    'pm_code': PostmasterType.code,
    'pm_schemes': parent_schemes,
}

def noop(apps, schema_editor):  # pragma: no cover
    pass

def create_pm_services(apps, schema_editor):  # pragma: no cover
    Channel = apps.get_model("channels", "Channel")
    queryset = Channel.objects.filter(
        is_active=True,
        channel_type=PostmasterType.code,
    ).exclude(
        Q(schemes=parent_schemes) | Q(parent_id__isnull=False)
    ).order_by('address')

    parent_id = None
    current_device_id = None
    for channel in queryset:
        if current_device_id != channel.address:
            current_device_id = channel.address
            #make new channel and get its ID in parent_id
            parent_name = channel.name[:channel.name.rfind('[')]
            parent_name += '['+parent_scheme+']'
            parent_config = channel.config
            create_args = dict(
                org=channel.org,
                country=channel.country,
                channel_type=channel.channel_type,
                name=parent_name,
                address=channel.address,
                config=parent_config,
                role=channel.role,
                schemes=parent_schemes,
                created_by=channel.created_by,
                modified_by=channel.modified_by,
                uuid=uuid4(),
            )
            parent_channel = Channel.objects.create(**create_args)
            parent_id = parent_channel.id
        #endif
        channel.parent_id = parent_id
        channel.save()
    #endfor
#enddef create_pm_services

def ensure_pm_service_device_name(apps, schema_editor):  # pragma: no cover
    Channel = apps.get_model("channels", "Channel")
    queryset = Channel.objects.filter(
        is_active=True,
        channel_type=PostmasterType.code,
        schemes=parent_schemes,
        parent_id__isnull=True,
    ).order_by('address')

    for channel in queryset:
        device_name = channel.name[:channel.name.rfind('[')-1]
        config = channel.config
        config["device_name"] = device_name
        channel.save(update_fields=('config',))
    #endfor
#enddef ensure_pm_service_device_name


class Migration(migrations.Migration):

    dependencies = [
        ("channels", "013901_index_address"),
    ]

    operations = [
        migrations.RunSQL(UPDATE_EXISTING_PM_SERVICE_CHANNELS_AS_PARENT_SQL),
        migrations.RunPython(create_pm_services, noop),
        migrations.RunPython(ensure_pm_service_device_name, noop),
    ]

#endclass Migration
