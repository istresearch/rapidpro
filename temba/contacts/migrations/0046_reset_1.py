# Generated by Django 1.10.5 on 2017-01-06 22:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import temba.utils.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Contact",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, help_text="Whether this item is active, use this instead of deleting"
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, help_text="When this item was originally created"),
                ),
                ("modified_on", models.DateTimeField(auto_now=True, help_text="When this item was last modified")),
                (
                    "uuid",
                    models.CharField(
                        db_index=True,
                        default=temba.utils.models.generate_uuid,
                        help_text="The unique identifier for this object",
                        max_length=36,
                        unique=True,
                        verbose_name="Unique Identifier",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="The name of this contact",
                        max_length=128,
                        null=True,
                        verbose_name="Name",
                    ),
                ),
                (
                    "is_blocked",
                    models.BooleanField(
                        default=False, help_text="Whether this contact has been blocked", verbose_name="Is Blocked"
                    ),
                ),
                (
                    "is_test",
                    models.BooleanField(
                        default=False, help_text="Whether this contact is for simulation", verbose_name="Is Test"
                    ),
                ),
                (
                    "is_stopped",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this contact has opted out of receiving messages",
                        verbose_name="Is Stopped",
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        blank=True,
                        help_text="The preferred language for this contact",
                        max_length=3,
                        null=True,
                        verbose_name="Language",
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="ContactField",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, help_text="Whether this item is active, use this instead of deleting"
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, help_text="When this item was originally created"),
                ),
                ("modified_on", models.DateTimeField(auto_now=True, help_text="When this item was last modified")),
                ("label", models.CharField(max_length=36, verbose_name="Label")),
                ("key", models.CharField(max_length=36, verbose_name="Key")),
                (
                    "value_type",
                    models.CharField(
                        choices=[
                            ("T", "Text"),
                            ("N", "Numeric"),
                            ("D", "Date & Time"),
                            ("S", "State"),
                            ("I", "District"),
                            ("W", "Ward"),
                        ],
                        default="T",
                        max_length=1,
                        verbose_name="Field Type",
                    ),
                ),
                ("show_in_table", models.BooleanField(default=False, verbose_name="Shown in Tables")),
            ],
            options={"abstract": False},
        ),
        migrations.CreateModel(
            name="ContactGroup",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, help_text="Whether this item is active, use this instead of deleting"
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, help_text="When this item was originally created"),
                ),
                ("modified_on", models.DateTimeField(auto_now=True, help_text="When this item was last modified")),
                (
                    "uuid",
                    models.CharField(
                        db_index=True,
                        default=temba.utils.models.generate_uuid,
                        help_text="The unique identifier for this object",
                        max_length=36,
                        unique=True,
                        verbose_name="Unique Identifier",
                    ),
                ),
                (
                    "name",
                    models.CharField(help_text="The name of this contact group", max_length=64, verbose_name="Name"),
                ),
                (
                    "group_type",
                    models.CharField(
                        choices=[
                            ("A", "All Contacts"),
                            ("B", "Blocked Contacts"),
                            ("S", "Stopped Contacts"),
                            ("U", "User Defined Groups"),
                        ],
                        default="U",
                        help_text="What type of group it is, either user defined or one of our system groups",
                        max_length=1,
                    ),
                ),
                (
                    "count",
                    models.IntegerField(
                        default=0, help_text="The number of contacts in this group", verbose_name="Count"
                    ),
                ),
                ("query", models.TextField(help_text="The membership query for this group", null=True)),
            ],
            options={"abstract": False},
            managers=[("all_groups", django.db.models.manager.Manager())],
        ),
        migrations.CreateModel(
            name="ContactGroupCount",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("count", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="ContactURN",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "urn",
                    models.CharField(
                        choices=[
                            ("tel", "Phone number"),
                            ("facebook", "Facebook identifier"),
                            ("twitter", "Twitter handle"),
                            ("viber", "Viber identifier"),
                            ("line", "LINE identifier"),
                            ("telegram", "Telegram identifier"),
                            ("mailto", "Email address"),
                            ("ext", "External identifier"),
                        ],
                        help_text="The Universal Resource Name as a string. ex: tel:+250788383383",
                        max_length=255,
                    ),
                ),
                (
                    "path",
                    models.CharField(help_text="The path component of our URN. ex: +250788383383", max_length=255),
                ),
                (
                    "scheme",
                    models.CharField(
                        help_text="The scheme for this URN, broken out for optimization reasons, ex: tel",
                        max_length=128,
                    ),
                ),
                (
                    "priority",
                    models.IntegerField(
                        default=50, help_text="The priority of this URN for the contact it is associated with"
                    ),
                ),
            ],
            options={"ordering": ("-priority", "id")},
        ),
        migrations.CreateModel(
            name="ExportContactsTask",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "is_active",
                    models.BooleanField(
                        default=True, help_text="Whether this item is active, use this instead of deleting"
                    ),
                ),
                (
                    "created_on",
                    models.DateTimeField(auto_now_add=True, help_text="When this item was originally created"),
                ),
                ("modified_on", models.DateTimeField(auto_now=True, help_text="When this item was last modified")),
                ("task_id", models.CharField(max_length=64, null=True)),
                ("is_finished", models.BooleanField(default=False, help_text="Whether this export has completed")),
                (
                    "uuid",
                    models.CharField(
                        help_text="The uuid used to name the resulting export file", max_length=36, null=True
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        help_text="The user which originally created this item",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contacts_exportcontactstask_creations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        help_text="The unique group to export",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="exports",
                        to="contacts.ContactGroup",
                    ),
                ),
                (
                    "modified_by",
                    models.ForeignKey(
                        help_text="The user which last modified this item",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contacts_exportcontactstask_modifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"abstract": False},
        ),
    ]
