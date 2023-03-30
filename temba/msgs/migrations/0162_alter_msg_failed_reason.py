# Generated by Django 3.2.9 on 2021-12-13 17:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("msgs", "0161_remove_response_to_and_connection"),
    ]

    operations = [
        migrations.AlterField(
            model_name="msg",
            name="failed_reason",
            field=models.CharField(
                choices=[
                    ("S", "Suspended"),
                    ("L", "Looping"),
                    ("E", "Error Limit"),
                    ("O", "Too Old"),
                    ("D", "No Destination"),
                ],
                max_length=1,
                null=True,
            ),
        ),
    ]
