# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-17 15:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0082_install_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlowPathRecentStep',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_uuid', models.UUIDField(help_text='Which flow node they came from')),
                ('to_uuid', models.UUIDField(help_text='Which flow node they went to')),
                ('left_on', models.DateTimeField(help_text='When they left the first node')),
                ('step', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recent_segments', to='flows.FlowStep')),
            ],
        ),
        migrations.RunSQL('CREATE INDEX flows_flowpathrecentstep_from_to_left '
                          'ON flows_flowpathrecentstep (from_uuid, to_uuid, left_on DESC)')
    ]
