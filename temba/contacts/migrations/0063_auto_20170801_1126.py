# Generated by Django 1.11.2 on 2017-08-01 11:26

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0062_populate_contact_field_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactfield',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
