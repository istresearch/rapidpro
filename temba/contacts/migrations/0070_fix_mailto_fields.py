# Generated by Django 1.11.6 on 2018-02-09 14:52

from django.db import migrations


def fix_mailto_fields(ContactField):
    mailto_fields = list(ContactField.objects.filter(key="mailto", is_active=True).select_related("org"))
    email_fields = list(ContactField.objects.filter(key="email", is_active=True).select_related("org"))
    if not mailto_fields:
        return

    print("Found %d mailto fields to fix..." % len(mailto_fields))

    orgs_with_email_field = {f.org for f in email_fields}

    for mailto_field in mailto_fields:
        if mailto_field.org not in orgs_with_email_field:
            mailto_field.key = "email"
            mailto_field.label = "Email"
            mailto_field.save(update_fields=("key", "label"))
            print(" > Renamed mailto field #%d for org #%d" % (mailto_field.id, mailto_field.org.id))
        else:
            print(
                " > Unable to rename mailto field #%d for org #%d because field called email already exists"
                % (mailto_field.id, mailto_field.org.id)
            )


def apply_manual():
    from temba.contacts.models import ContactField

    fix_mailto_fields(ContactField)


def apply_as_migration(apps, schema_editor):
    ContactField = apps.get_model("contacts", "ContactField")
    fix_mailto_fields(ContactField)


class Migration(migrations.Migration):

    dependencies = [("contacts", "0069_iso639-3")]

    operations = [migrations.RunPython(apply_as_migration)]
