# Generated by Django 2.2.10 on 2021-01-05 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0122_auto_20200323_2134'),
        ('channels', '0122_populate_allow_international'),
        ('channels', '0123_auto_20201026_1945'),
    ]

    operations = [
        migrations.AlterField(
            model_name="channellog", name="id", field=models.BigAutoField(primary_key=True, serialize=False)
        ),
    ]
