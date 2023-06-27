# Generated by Django 4.0.3 on 2022-03-29 19:07

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0157_update_group_type"),
        ("flows", "0277_flowrun_flows_flowrun_contacts_at_node"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flowrun",
            name="contact",
            field=models.ForeignKey(
                db_index=False, on_delete=django.db.models.deletion.PROTECT, related_name="runs", to="contacts.contact"
            ),
        ),
        migrations.AddIndex(
            model_name="flowrun",
            index=models.Index(fields=["contact"], include=("flow",), name="flows_flowrun_contact_inc_flow"),
        ),
    ]
