# Generated by Django 1.11.2 on 2017-06-29 07:05

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("flows", "0106_auto_20170622_1541")]

    operations = [
        migrations.AddField(model_name="flowrun", name="uuid", field=models.UUIDField(null=True)),
        migrations.AlterField(
            model_name="flowrun", name="uuid", field=models.UUIDField(default=uuid.uuid4, null=True)
        ),
    ]
