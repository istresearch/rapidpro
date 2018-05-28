# Generated by Django 1.10.5 on 2017-06-08 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("flows", "0101_auto_20170606_1326")]

    operations = [
        migrations.AlterField(
            model_name="flowstep",
            name="rule_value",
            field=models.TextField(
                help_text="The value that was matched in our category for this ruleset, null on ActionSets", null=True
            ),
        )
    ]
