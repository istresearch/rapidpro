# Generated by Django 1.10.5 on 2017-02-15 06:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("flows", "0088_drop_squash_functions")]

    operations = [
        migrations.AddField(
            model_name="exportflowresultstask",
            name="status",
            field=models.CharField(
                choices=[("P", "Pending"), ("O", "Processing"), ("C", "Complete"), ("F", "Failed")],
                default="P",
                max_length=1,
            ),
        ),
        migrations.AlterField(
            model_name="exportflowresultstask",
            name="org",
            field=models.ForeignKey(
                help_text="The organization of the user.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="exportflowresultstasks",
                to="orgs.Org",
            ),
        ),
        migrations.RemoveField(model_name="exportflowresultstask", name="task_id"),
    ]
