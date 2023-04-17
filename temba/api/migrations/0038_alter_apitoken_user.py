# Generated by Django 4.0.4 on 2022-05-16 22:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orgs", "0096_user"),
        ("api", "0035_alter_resthook_created_by_alter_resthook_modified_by_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="apitoken",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, related_name="api_tokens", to="orgs.user"
            ),
        ),
    ]
