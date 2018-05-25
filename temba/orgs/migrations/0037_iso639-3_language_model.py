from django.db import migrations, transaction

from temba.utils.languages import iso6392_to_iso6393, get_language_name

country_code_cache = {}


def migrate_language(language_qs):
    with transaction.atomic():
        for language in language_qs.only("org__country__name", "iso_code", "name").iterator():
            try:
                country_code = language.org.get_country_code()
            except AttributeError:
                country_code = None

            new_iso_code = iso6392_to_iso6393(language.iso_code, country_code=country_code)
            new_lang_name = get_language_name(new_iso_code)

            if new_lang_name is None:
                raise ValueError(
                    "(lang_id={}) Cannot get language name for iso_code: {}".format(language.id, new_iso_code)
                )

            if new_iso_code != language.iso_code or new_lang_name != language.name:
                print(
                    "Updated: language_id=",
                    language.id,
                    "org__country",
                    country_code,
                    "old_iso_code=",
                    language.iso_code,
                    "=> new_iso_code=",
                    new_iso_code,
                    "old_name=",
                    language.name,
                    "=> new_lang_name",
                    new_lang_name,
                )
                language.iso_code = new_iso_code
                language.name = new_lang_name
                language.save(update_fields=("name", "iso_code"))


def apply_manual():
    from temba.orgs.models import Language

    language_qs = Language.objects.select_related("org", "org__country")
    migrate_language(language_qs)


def apply_as_migration(apps, schema_editor):
    Language = apps.get_model("orgs", "Language")
    language_qs = Language.objects.select_related("org", "org__country")
    migrate_language(language_qs)


class Migration(migrations.Migration):

    dependencies = [("orgs", "0036_ensure_anon_user_exists")]

    operations = [migrations.RunPython(apply_as_migration)]
