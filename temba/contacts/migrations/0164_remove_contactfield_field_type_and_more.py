# Generated by Django 4.0.3 on 2022-04-18 23:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0163_alter_contactgroup_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="contactfield",
            name="field_type",
        ),
        migrations.RemoveField(
            model_name="contactfield",
            name="label",
        ),
    ]
