# Generated by Django 4.0.4 on 2022-05-03 17:58

from django.db import migrations, models

import temba.utils.fields
import temba.utils.uuid


class Migration(migrations.Migration):

    dependencies = [
        ("classifiers", "0005_alter_classifier_created_by_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="classifier",
            name="name",
            field=models.CharField(max_length=64, validators=[temba.utils.fields.NameValidator(64)]),
        ),
        migrations.AlterField(
            model_name="classifier",
            name="uuid",
            field=models.UUIDField(default=temba.utils.uuid.uuid4, unique=True),
        ),
    ]
