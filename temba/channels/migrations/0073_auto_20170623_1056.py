# Generated by Django 1.11.2 on 2017-06-23 10:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0072_migrate_twilio_apps'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='channel_type',
            field=models.CharField(max_length=3, verbose_name='Channel Type'),
        ),
    ]
