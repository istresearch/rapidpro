# Generated by Django 3.2.6 on 2021-08-02 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("locations", "0019_remove_adminboundary_geometry"),
    ]

    operations = [
        migrations.AlterField(
            model_name="adminboundary",
            name="lft",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="adminboundary",
            name="rght",
            field=models.PositiveIntegerField(editable=False),
        ),
    ]
