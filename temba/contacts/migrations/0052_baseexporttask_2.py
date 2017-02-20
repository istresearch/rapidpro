# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-15 06:57
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.models import Case, Value, When
from temba.utils.models import generate_uuid


def populate_export_status(apps, schema_editor):
    ExportContactsTask = apps.get_model('contacts', 'ExportContactsTask')
    ExportContactsTask.objects.update(status=Case(When(is_finished=True, then=Value('C')), default=Value('O')))


def populate_uuid(apps, schema_editor):
    ExportContactsTask = apps.get_model('contacts', 'ExportContactsTask')
    for task in ExportContactsTask.objects.filter(uuid=None):
        task.uuid = generate_uuid()
        task.save(update_fields=('uuid',))


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0051_baseexporttask_1'),
    ]

    operations = [
        migrations.RunPython(populate_export_status),
        migrations.RunPython(populate_uuid),
        migrations.RemoveField(
            model_name='exportcontactstask',
            name='is_finished',
        ),
        migrations.AlterField(
            model_name='exportcontactstask',
            name='uuid',
            field=models.CharField(db_index=True, default=generate_uuid,
                                   help_text='The unique identifier for this object', max_length=36, unique=True,
                                   verbose_name='Unique Identifier'),
        ),
    ]
