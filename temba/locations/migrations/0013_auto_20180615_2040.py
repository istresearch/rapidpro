# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-06-15 20:40
from __future__ import unicode_literals

import mptt.fields

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("locations", "0012_path_not_null")]

    operations = [
        migrations.AlterField(
            model_name="adminboundary",
            name="parent",
            field=mptt.fields.TreeForeignKey(
                blank=True,
                help_text="The parent to this political boundary if any",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="children",
                to="locations.AdminBoundary",
            ),
        ),
        migrations.AlterField(
            model_name="boundaryalias",
            name="boundary",
            field=models.ForeignKey(
                help_text="The admin boundary this alias applies to",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="aliases",
                to="locations.AdminBoundary",
            ),
        ),
        migrations.AlterField(
            model_name="boundaryalias",
            name="created_by",
            field=models.ForeignKey(
                help_text="The user which originally created this item",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="locations_boundaryalias_creations",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="boundaryalias",
            name="modified_by",
            field=models.ForeignKey(
                help_text="The user which last modified this item",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="locations_boundaryalias_modifications",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="boundaryalias",
            name="org",
            field=models.ForeignKey(
                help_text="The org that owns this alias", on_delete=django.db.models.deletion.PROTECT, to="orgs.Org"
            ),
        ),
    ]
