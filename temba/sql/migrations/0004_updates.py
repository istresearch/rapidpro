# Generated by Django 4.0.3 on 2022-03-10 17:56

from django.db import migrations

from . import InstallSQL


class Migration(migrations.Migration):

    dependencies = [
        ("sql", "0003_fix_02_skip"),
    ]

    operations = [
        InstallSQL("0004_functions"),
        InstallSQL("0004_indexes"),
        InstallSQL("0004_triggers"),
    ]
