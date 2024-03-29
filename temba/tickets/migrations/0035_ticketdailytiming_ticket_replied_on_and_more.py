# Generated by Django 4.0.4 on 2022-05-17 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orgs", "0096_user"),
        ("tickets", "0034_backfill_ticket_daily_counts"),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketDailyTiming",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("is_squashed", models.BooleanField(default=False)),
                ("count_type", models.CharField(max_length=1)),
                ("scope", models.CharField(max_length=32)),
                ("count", models.IntegerField()),
                ("day", models.DateField()),
                ("seconds", models.BigIntegerField()),
            ],
        ),
        migrations.AddField(
            model_name="ticket",
            name="replied_on",
            field=models.DateTimeField(null=True),
        ),
        migrations.AddIndex(
            model_name="ticketdailytiming",
            index=models.Index(fields=["count_type", "scope", "day"], name="tickets_dailytiming_type_scope"),
        ),
        migrations.AddIndex(
            model_name="ticketdailytiming",
            index=models.Index(
                condition=models.Q(("is_squashed", False)),
                fields=["count_type", "scope", "day"],
                name="tickets_dailytiming_unsquashed",
            ),
        ),
    ]
