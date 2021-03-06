# Generated by Django 2.2.4 on 2019-08-22 18:32

from datetime import datetime

import pytz

from django.db import migrations


def noop(apps, schema_editor):  # pragma: no cover
    pass


def populate_days_of_week(apps, schema_editor):  # pragma: no cover
    Schedule = apps.get_model("schedules", "Schedule")
    WEEKDAYS = "MTWRFSU"
    updated = 0

    for s in Schedule.objects.filter(repeat_period="W"):
        if s.repeat_days:
            repeat_days_of_week = ""

            bitmask_number = bin(s.repeat_days)
            for idx in range(7):
                power = bin(pow(2, idx + 1))
                if bin(int(bitmask_number, 2) & int(power, 2)) == power:
                    repeat_days_of_week += WEEKDAYS[idx]

            s.repeat_days_of_week = repeat_days_of_week
            s.save(update_fields=["repeat_days_of_week"])

            updated += 1

    if updated > 0:
        print(f"updated {updated} weekly schedules")

    updated = (
        Schedule.objects.exclude(repeat_period="O").filter(repeat_minute_of_hour=None).update(repeat_minute_of_hour=0)
    )
    if updated > 0:
        print(f"updated {updated} schedules with missing minute of hour")

    # repeat_hour_of_day was previously in UTC time, change that to org timezone
    updated = 0
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0, tzinfo=pytz.utc)
    for s in Schedule.objects.exclude(repeat_period="O"):
        tz = s.org.timezone
        hour_time = now.replace(hour=s.repeat_hour_of_day)
        local_now = tz.normalize(hour_time.astimezone(tz))
        s.repeat_hour_of_day = local_now.hour
        s.save(update_fields=["repeat_hour_of_day"])

        updated += 1

    if updated > 0:
        print(f"updated {updated} hour of day on repeating schedules")


class Migration(migrations.Migration):

    dependencies = [("schedules", "0010_populate_org")]

    operations = [migrations.RunPython(populate_days_of_week, noop)]
