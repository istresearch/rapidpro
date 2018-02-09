# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-02-02 12:28
from __future__ import unicode_literals

import collections
from django.db import migrations
import temba.utils.models


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0145_update_path_trigger'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionset',
            name='actions',
            field=temba.utils.models.JSONAsTextField(help_text='The JSON encoded actions for this action set'),
        ),
        migrations.AlterField(
            model_name='exportflowresultstask',
            name='config',
            field=temba.utils.models.JSONAsTextField(help_text='Any configuration options for this flow export', null=True),
        ),
        migrations.AlterField(
            model_name='flow',
            name='metadata',
            field=temba.utils.models.JSONAsTextField(blank=True, help_text='Any extra metadata attached to this flow, strictly used by the user interface.', null=True, default=dict),
        ),
        migrations.AlterField(
            model_name='flowrevision',
            name='definition',
            field=temba.utils.models.JSONAsTextField(help_text='The JSON flow definition'),
        ),
        migrations.AlterField(
            model_name='flowrun',
            name='fields',
            field=temba.utils.models.JSONAsTextField(blank=True, help_text='A JSON representation of any custom flow values the user has saved away', null=True, object_pairs_hook=collections.OrderedDict, default=dict),
        ),
        migrations.AlterField(
            model_name='flowrun',
            name='path',
            field=temba.utils.models.JSONAsTextField(help_text='The path taken during this flow run in JSON format', null=True, default=list),
        ),
        migrations.AlterField(
            model_name='flowrun',
            name='results',
            field=temba.utils.models.JSONAsTextField(help_text='The results collected during this flow run in JSON format', null=True, default=dict),
        ),
        migrations.AlterField(
            model_name='flowstart',
            name='extra',
            field=temba.utils.models.JSONAsTextField(help_text='Any extra parameters to pass to the flow start (json)', null=True),
        ),
        migrations.AlterField(
            model_name='ruleset',
            name='config',
            field=temba.utils.models.JSONAsTextField(help_text='RuleSet type specific configuration', null=True, verbose_name='Ruleset Configuration', default=dict),
        ),
        migrations.AlterField(
            model_name='ruleset',
            name='rules',
            field=temba.utils.models.JSONAsTextField(help_text='The JSON encoded actions for this action set', default=list),
        ),
    ]
