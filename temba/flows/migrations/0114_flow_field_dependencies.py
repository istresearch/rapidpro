# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-12 18:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0067_auto_20170808_1852'),
        ('flows', '0113_auto_20171012_1839'),
    ]

    operations = [
        migrations.AddField(
            model_name='flow',
            name='field_dependencies',
            field=models.ManyToManyField(blank=True, help_text='Any fields this flow depends on', related_name='dependent_flows', to='contacts.ContactField', verbose_name=''),
        ),
    ]
