from copy import deepcopy

from django.db import migrations

from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES
from temba.channels.types.postmaster import PostmasterType


UPDATE_EXISTING_PM_SERVICE_CHANNELS_AS_PARENT_SQL = """
UPDATE channels_channel ch
   SET parent_id=par.id FROM channels_channel par
         WHERE par.address=ch.address
           AND par.is_active=ch.is_active
           AND par.channel_type = PostmasterType.code
           AND par.schemes IS NULL
           AND ch.channel_type = par.channel_type
           AND ch.schemes != par.schemes
           AND ch.is_active=True
"""


def noop(apps, schema_editor):  # pragma: no cover
    pass

def create_pm_services(apps, schema_editor):  # pragma: no cover
    Channel = apps.get_model("channels", "Channel")
    queryset = Channel.objects.filter(
        is_active=True,
        channel_type=PostmasterType.code,
    ).exclude(
        schemes='{'+PM_CHANNEL_MODES['PM'].scheme+'}',
        parent_id=None,
    ).order_by('address')

    parent_chat_mode = 'PM'
    parent_scheme = PM_CHANNEL_MODES[parent_chat_mode].scheme
    parent_id = None
    current_device_id = None
    for channel in queryset:
        if current_device_id != channel.address:
            current_device_id = channel.address
            #make new channel and get its ID in parent_id
            parent_channel = deepcopy(channel)
            parent_channel.id = None
            parent_channel.schemes = '{'+parent_scheme+'}'
            parent_channel.name = parent_channel.name[:parent_channel.name.rfind('[')]
            parent_channel.name += '['+parent_scheme+']'
            channel.config["chat_mode"] = parent_chat_mode
            parent_channel.save()
            parent_id = parent_channel.id
        #endif
        channel.update(parent_id=parent_id)
    #endfor
#enddef create_pm_services


class Migration(migrations.Migration):

    dependencies = [
        ("channels", "013901_index_address"),
    ]

    operations = [
        migrations.RunSQL(UPDATE_EXISTING_PM_SERVICE_CHANNELS_AS_PARENT_SQL),
        migrations.RunPython(create_pm_services, noop)
    ]

#endclass Migration
