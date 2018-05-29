# Generated by Django 1.11.2 on 2017-08-11 15:11

import django.contrib.postgres.fields
from django.db import migrations, models


def update_twitter_channels_schemes(apps, schema_editor):
    Channel = apps.get_model("channels", "Channel")

    Channel.objects.filter(channel_type__in=["TT", "TWT"]).update(schemes=["twitter", "twitterid"])


class Migration(migrations.Migration):

    atomic = False

    dependencies = [("channels", "0074_channel_schemes")]

    operations = [
        migrations.RemoveField(model_name="channel", name="scheme"),
        migrations.AlterField(
            model_name="channel",
            name="schemes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=16),
                default=["tel"],
                help_text="The URN schemes this channel supports",
                size=None,
                verbose_name="URN Schemes",
            ),
        ),
        migrations.RunPython(update_twitter_channels_schemes),
    ]
