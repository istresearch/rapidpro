# Generated by Django 1.10.5 on 2017-01-06 23:29

from django.db import migrations

from temba.sql import InstallSQL


class Migration(migrations.Migration):

    dependencies = [("msgs", "0075_reset_1")]

    operations = [InstallSQL("0076_msgs")]
