from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("channels", "0139_channel_is_system"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="channel",
            index=models.Index(
                fields=["address"],
                name="idx_address",
            ),
        ),
    ]
