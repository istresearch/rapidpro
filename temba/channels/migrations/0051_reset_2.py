# Generated by Django 1.10.5 on 2017-01-06 22:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contacts", "0046_reset_1"),
        ("channels", "0050_reset_1"),
    ]

    operations = [
        migrations.AddField(
            model_name="channelsession",
            name="contact",
            field=models.ForeignKey(
                help_text="Who this session is with",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="sessions",
                to="contacts.Contact",
            ),
        ),
        migrations.AddField(
            model_name="channelsession",
            name="contact_urn",
            field=models.ForeignKey(
                help_text="The URN this session is communicating with",
                on_delete=django.db.models.deletion.CASCADE,
                to="contacts.ContactURN",
                verbose_name="Contact URN",
            ),
        ),
        migrations.AddField(
            model_name="channelsession",
            name="created_by",
            field=models.ForeignKey(
                help_text="The user which originally created this item",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="channels_channelsession_creations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
