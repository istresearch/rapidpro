# Generated by Django 2.1.9 on 2019-07-30 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0208_flowsession_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='flowstart',
            name='query',
            field=models.TextField(null=True),
        ),
    ]
