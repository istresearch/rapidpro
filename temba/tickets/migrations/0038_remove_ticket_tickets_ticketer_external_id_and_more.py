# Generated by Django 4.0.4 on 2022-06-10 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0037_alter_ticket_assignee_alter_ticketcount_assignee_and_more"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="ticket",
            name="tickets_ticketer_external_id",
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(
                condition=models.Q(("external_id__isnull", False)),
                fields=["ticketer", "external_id"],
                name="tickets_ticketer_external_id",
            ),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["-modified_on"], name="tickets_modified_on"),
        ),
        migrations.AddIndex(
            model_name="ticket",
            index=models.Index(fields=["contact", "-modified_on"], name="tickets_contact_modified_on"),
        ),
    ]
