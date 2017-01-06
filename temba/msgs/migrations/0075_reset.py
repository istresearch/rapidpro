# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-06 22:38
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import temba.utils.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contacts', '0046_reset_1'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('channels', '0051_reset_3'),
        ('schedules', '0003_reset'),
        ('orgs', '0029_reset'),
    ]

    operations = [
        migrations.CreateModel(
            name='Broadcast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipient_count', models.IntegerField(help_text='Number of urns which received this broadcast', null=True, verbose_name='Number of recipients')),
                ('text', models.TextField(help_text='The message to send out', max_length=640, verbose_name='Text')),
                ('status', models.CharField(choices=[('I', 'Initializing'), ('P', 'Pending'), ('Q', 'Queued'), ('W', 'Wired'), ('S', 'Sent'), ('D', 'Delivered'), ('H', 'Handled'), ('E', 'Error Sending'), ('F', 'Failed Sending'), ('R', 'Resent message')], default='I', help_text='The current status for this broadcast', max_length=1, verbose_name='Status')),
                ('language_dict', models.TextField(help_text='The localized versions of the broadcast', null=True, verbose_name='Translations')),
                ('base_language', models.CharField(blank=True, help_text='The language used to send this to contacts without a language', max_length=4, null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this broadcast is active')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When this broadcast was created')),
                ('modified_on', models.DateTimeField(auto_now=True, help_text='When this item was last modified')),
                ('purged', models.BooleanField(default=False, help_text='If the messages for this broadcast have been purged')),
                ('channel', models.ForeignKey(help_text='Channel to use for message sending', null=True, on_delete=django.db.models.deletion.CASCADE, to='channels.Channel', verbose_name='Channel')),
                ('contacts', models.ManyToManyField(help_text='Individual contacts included in this message', related_name='addressed_broadcasts', to='contacts.Contact', verbose_name='Contacts')),
                ('created_by', models.ForeignKey(help_text='The user which originally created this item', on_delete=django.db.models.deletion.CASCADE, related_name='msgs_broadcast_creations', to=settings.AUTH_USER_MODEL)),
                ('groups', models.ManyToManyField(help_text='The groups to send the message to', related_name='addressed_broadcasts', to='contacts.ContactGroup', verbose_name='Groups')),
                ('modified_by', models.ForeignKey(help_text='The user which last modified this item', on_delete=django.db.models.deletion.CASCADE, related_name='msgs_broadcast_modifications', to=settings.AUTH_USER_MODEL)),
                ('org', models.ForeignKey(help_text='The org this broadcast is connected to', on_delete=django.db.models.deletion.CASCADE, to='orgs.Org', verbose_name='Org')),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='msgs.Broadcast', verbose_name='Parent')),
            ],
        ),
        migrations.CreateModel(
            name='BroadcastRecipient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purged_status', models.CharField(help_text="Used when broadcast is purged to record contact's message's state", max_length=1, null=True)),
                ('broadcast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='msgs.Broadcast')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contacts.Contact')),
            ],
            options={
                'db_table': 'msgs_broadcast_recipients',
            },
        ),
        migrations.CreateModel(
            name='ExportMessagesTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this item is active, use this instead of deleting')),
                ('created_on', models.DateTimeField(auto_now_add=True, help_text='When this item was originally created')),
                ('modified_on', models.DateTimeField(auto_now=True, help_text='When this item was last modified')),
                ('start_date', models.DateField(blank=True, help_text='The date for the oldest message to export', null=True)),
                ('end_date', models.DateField(blank=True, help_text='The date for the newest message to export', null=True)),
                ('task_id', models.CharField(max_length=64, null=True)),
                ('is_finished', models.BooleanField(default=False, help_text='Whether this export is finished running')),
                ('uuid', models.CharField(help_text='The uuid used to name the resulting export file', max_length=36, null=True)),
                ('created_by', models.ForeignKey(help_text='The user which originally created this item', on_delete=django.db.models.deletion.CASCADE, related_name='msgs_exportmessagestask_creations', to=settings.AUTH_USER_MODEL)),
                ('groups', models.ManyToManyField(to='contacts.ContactGroup')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this item is active, use this instead of deleting')),
                ('created_on', models.DateTimeField(auto_now_add=True, help_text='When this item was originally created')),
                ('modified_on', models.DateTimeField(auto_now=True, help_text='When this item was last modified')),
                ('uuid', models.CharField(db_index=True, default=temba.utils.models.generate_uuid, help_text='The unique identifier for this object', max_length=36, unique=True, verbose_name='Unique Identifier')),
                ('name', models.CharField(help_text='The name of this label', max_length=64, verbose_name='Name')),
                ('label_type', models.CharField(choices=[('F', 'Folder of labels'), ('L', 'Regular label')], default='L', help_text='Label type', max_length=1)),
                ('visible_count', models.PositiveIntegerField(default=0, help_text='Number of non-archived messages with this label')),
                ('created_by', models.ForeignKey(help_text='The user which originally created this item', on_delete=django.db.models.deletion.CASCADE, related_name='msgs_label_creations', to=settings.AUTH_USER_MODEL)),
                ('folder', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='msgs.Label', verbose_name='Folder')),
                ('modified_by', models.ForeignKey(help_text='The user which last modified this item', on_delete=django.db.models.deletion.CASCADE, related_name='msgs_label_modifications', to=settings.AUTH_USER_MODEL)),
                ('org', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orgs.Org')),
            ],
            managers=[
                ('all_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='Msg',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='The actual message content that was sent', max_length=640, verbose_name='Text')),
                ('priority', models.IntegerField(default=500, help_text='The priority for this message to be sent, higher is higher priority')),
                ('created_on', models.DateTimeField(db_index=True, help_text='When this message was created', verbose_name='Created On')),
                ('modified_on', models.DateTimeField(auto_now=True, help_text='When this message was last modified', null=True, verbose_name='Modified On')),
                ('sent_on', models.DateTimeField(blank=True, help_text='When this message was sent to the endpoint', null=True, verbose_name='Sent On')),
                ('queued_on', models.DateTimeField(blank=True, help_text='When this message was queued to be sent or handled.', null=True, verbose_name='Queued On')),
                ('direction', models.CharField(choices=[('I', 'Incoming'), ('O', 'Outgoing')], help_text='The direction for this message, either incoming or outgoing', max_length=1, verbose_name='Direction')),
                ('status', models.CharField(choices=[('I', 'Initializing'), ('P', 'Pending'), ('Q', 'Queued'), ('W', 'Wired'), ('S', 'Sent'), ('D', 'Delivered'), ('H', 'Handled'), ('E', 'Error Sending'), ('F', 'Failed Sending'), ('R', 'Resent message')], db_index=True, default='P', help_text='The current status for this message', max_length=1, verbose_name='Status')),
                ('visibility', models.CharField(choices=[('V', 'Visible'), ('A', 'Archived'), ('D', 'Deleted')], db_index=True, default='V', help_text='The current visibility of this message, either visible, archived or deleted', max_length=1, verbose_name='Visibility')),
                ('has_template_error', models.BooleanField(default=False, help_text='Whether data for variable substitution are missing', verbose_name='Has Template Error')),
                ('msg_type', models.CharField(choices=[('I', 'Inbox Message'), ('F', 'Flow Message'), ('V', 'IVR Message')], help_text='The type of this message', max_length=1, null=True, verbose_name='Message Type')),
                ('msg_count', models.IntegerField(default=1, help_text='The number of messages that were used to send this message, calculated on Twilio channels', verbose_name='Message Count')),
                ('error_count', models.IntegerField(default=0, help_text='The number of times this message has errored', verbose_name='Error Count')),
                ('next_attempt', models.DateTimeField(auto_now_add=True, help_text='When we should next attempt to deliver this message', verbose_name='Next Attempt')),
                ('external_id', models.CharField(blank=True, help_text='External id used for integrating with callbacks from other APIs', max_length=255, null=True, verbose_name='External ID')),
                ('media', models.URLField(blank=True, help_text='The media associated with this message if any', max_length=255, null=True)),
                ('broadcast', models.ForeignKey(blank=True, help_text='If this message was sent to more than one recipient', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='msgs', to='msgs.Broadcast', verbose_name='Broadcast')),
                ('channel', models.ForeignKey(help_text='The channel object that this message is associated with', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='msgs', to='channels.Channel', verbose_name='Channel')),
                ('contact', models.ForeignKey(help_text='The contact this message is communicating with', on_delete=django.db.models.deletion.CASCADE, related_name='msgs', to='contacts.Contact', verbose_name='Contact')),
                ('contact_urn', models.ForeignKey(help_text='The URN this message is communicating with', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='msgs', to='contacts.ContactURN', verbose_name='Contact URN')),
                ('labels', models.ManyToManyField(help_text='Any labels on this message', related_name='msgs', to='msgs.Label', verbose_name='Labels')),
                ('org', models.ForeignKey(help_text='The org this message is connected to', on_delete=django.db.models.deletion.CASCADE, related_name='msgs', to='orgs.Org', verbose_name='Org')),
                ('response_to', models.ForeignKey(blank=True, db_index=False, help_text='The message that this message is in reply to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='msgs.Msg', verbose_name='Response To')),
                ('topup', models.ForeignKey(blank=True, help_text='The topup that this message was deducted from', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='msgs', to='orgs.TopUp')),
            ],
            options={
                'ordering': ['-created_on', '-pk'],
            },
        ),
        migrations.CreateModel(
            name='SystemLabel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label_type', models.CharField(choices=[('I', 'Inbox'), ('W', 'Flows'), ('A', 'Archived'), ('O', 'Outbox'), ('S', 'Sent'), ('X', 'Failed'), ('E', 'Scheduled'), ('C', 'Calls')], max_length=1)),
                ('count', models.IntegerField(default=0, help_text='Number of items with this system label')),
                ('org', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='system_labels', to='orgs.Org')),
            ],
        ),
        migrations.AddField(
            model_name='exportmessagestask',
            name='label',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='msgs.Label'),
        ),
        migrations.AddField(
            model_name='exportmessagestask',
            name='modified_by',
            field=models.ForeignKey(help_text='The user which last modified this item', on_delete=django.db.models.deletion.CASCADE, related_name='msgs_exportmessagestask_modifications', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='exportmessagestask',
            name='org',
            field=models.ForeignKey(help_text='The organization of the user.', on_delete=django.db.models.deletion.CASCADE, to='orgs.Org'),
        ),
        migrations.AddField(
            model_name='broadcast',
            name='recipients',
            field=models.ManyToManyField(help_text='The contacts which received this message', related_name='broadcasts', through='msgs.BroadcastRecipient', to='contacts.Contact', verbose_name='Recipients'),
        ),
        migrations.AddField(
            model_name='broadcast',
            name='schedule',
            field=models.OneToOneField(help_text='Our recurring schedule if we have one', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='broadcast', to='schedules.Schedule', verbose_name='Schedule'),
        ),
        migrations.AddField(
            model_name='broadcast',
            name='urns',
            field=models.ManyToManyField(help_text='Individual URNs included in this message', related_name='addressed_broadcasts', to='contacts.ContactURN', verbose_name='URNs'),
        ),
        migrations.AlterIndexTogether(
            name='systemlabel',
            index_together=set([('org', 'label_type')]),
        ),
        migrations.AlterUniqueTogether(
            name='label',
            unique_together=set([('org', 'name')]),
        ),
    ]
