# Generated by Django 2.2.4 on 2020-05-11 21:08

from django.db import migrations
import temba.utils.models


class Migration(migrations.Migration):

    dependencies = [
        ('msgs', '0138_remove_broadcast_recipient_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='broadcast',
            name='text',
            field=temba.utils.models.TranslatableField(help_text='The localized versions of the message text', max_length=4096, verbose_name='Translations'),
        ),
    ]