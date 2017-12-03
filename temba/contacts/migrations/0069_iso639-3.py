# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-21 15:23
from __future__ import unicode_literals, print_function

from django.db import migrations, transaction

from temba.utils.languages import iso6392_to_iso6393


def migrate_language(contact_qs):
    with transaction.atomic():
        # if we define exact fields that are used it improves the execution speed
        # the execution was 'blocked' by Python while it was loading 30+ fields from db relations
        # and two of those fields are large binary blobs - geometry
        for contact in contact_qs.only('org__country__name', 'language').iterator():
            try:
                country_code = contact.org.get_country_code()
            except AttributeError:
                country_code = None

            new_language = iso6392_to_iso6393(contact.language, country_code=country_code)

            if new_language != contact.language:
                print(
                    'Updated: contact_id=', contact.id, 'org__country__name', contact.org.country.name,
                    'old_lang=', contact.language, '=> new_lang=', new_language
                )
                contact.language = new_language
                contact.save(update_fields=('language', ))


def apply_manual():
    from temba.contacts.models import Contact
    contact_qs = Contact.objects.filter(language__isnull=False).select_related('org', 'org__country')
    migrate_language(contact_qs)


def apply_as_migration(apps, schema_editor):
    Contact = apps.get_model('contacts', 'Contact')
    contact_qs = Contact.objects.filter(language__isnull=False).select_related('org', 'org__country')
    migrate_language(contact_qs)


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0068_rewrite_dynamic_queries'),
    ]

    operations = [
        migrations.RunPython(apply_as_migration)
    ]
