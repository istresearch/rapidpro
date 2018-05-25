# Generated by Django 1.10.6 on 2017-04-06 17:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("msgs", "0087_remove_label_visible_count")]

    operations = [
        migrations.AddField(
            model_name="broadcast",
            name="send_all",
            field=models.NullBooleanField(help_text="Whether this broadcast should send to all URNs for each contact"),
        )
    ]
