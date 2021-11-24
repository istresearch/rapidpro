# Generated by Django 2.2.4 on 2020-04-08 20:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("flows", "0225_populate_template_deps")]

    operations = [
        migrations.AddField(
            model_name="flowstart",
            name="org",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT, related_name="flow_starts", to="orgs.Org"
            ),
        ),
        migrations.RemoveField(model_name="flowstart", name="is_active"),
        migrations.RemoveField(model_name="flowstart", name="modified_by"),
    ]
