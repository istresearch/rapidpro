# Generated by Django 2.2.4 on 2019-08-22 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("orgs", "0058_auto_20190723_2129"), ("schedules", "0008_initial")]

    operations = [
        migrations.AddField(
            model_name="schedule", name="repeat_days_of_week", field=models.CharField(max_length=7, null=True)
        ),
        migrations.AlterField(model_name="schedule", name="last_fire", field=models.DateTimeField(null=True)),
        migrations.AlterField(model_name="schedule", name="next_fire", field=models.DateTimeField(null=True)),
        migrations.AlterField(model_name="schedule", name="repeat_day_of_month", field=models.IntegerField(null=True)),
        migrations.AlterField(
            model_name="schedule", name="repeat_days", field=models.IntegerField(default=0, null=True)
        ),
        migrations.AlterField(model_name="schedule", name="repeat_hour_of_day", field=models.IntegerField(null=True)),
        migrations.AlterField(
            model_name="schedule", name="repeat_minute_of_hour", field=models.IntegerField(null=True)
        ),
        migrations.AlterField(
            model_name="schedule",
            name="repeat_period",
            field=models.CharField(
                choices=[("O", "Never"), ("D", "Daily"), ("W", "Weekly"), ("M", "Monthly")], default="O", max_length=1
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="schedule",
            name="status",
            field=models.CharField(
                choices=[("U", "Unscheduled"), ("S", "Scheduled")], default="U", max_length=1, null=True
            ),
        ),
        migrations.AddField(
            model_name="schedule",
            name="org",
            field=models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to="orgs.Org"),
        ),
    ]
