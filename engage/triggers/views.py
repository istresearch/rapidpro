from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import MonkeyPatcher

from temba.channels.models import Channel
from temba.contacts.models import ContactURN
from temba.triggers.views import TriggerCRUDL


class TriggerCreateOverrides(MonkeyPatcher):
    patch_class = TriggerCRUDL.Create

    def derive_formax_sections(self: TriggerCRUDL.Create, formax, context):
        def add_section(name, url, icon):
            formax.add_section(name, reverse(url), icon=icon, action="redirect", button=_("Create Trigger"))

        org_schemes = self.org.get_schemes(Channel.ROLE_RECEIVE)
        add_section("trigger-keyword", "triggers.trigger_create_keyword", "icon-tree")
        add_section("trigger-register", "triggers.trigger_create_register", "icon-users-2")
        add_section("trigger-catchall", "triggers.trigger_create_catchall", "icon-bubble")
        add_section("trigger-schedule", "triggers.trigger_create_schedule", "icon-clock")
        add_section("trigger-inboundcall", "triggers.trigger_create_inbound_call", "icon-phone2")
        add_section("trigger-missedcall", "triggers.trigger_create_missed_call", "icon-phone")

        if ContactURN.SCHEMES_SUPPORTING_NEW_CONVERSATION.intersection(org_schemes):
            add_section("trigger-new-conversation", "triggers.trigger_create_new_conversation", "icon-bubbles-2")

        if ContactURN.SCHEMES_SUPPORTING_REFERRALS.intersection(org_schemes):
            add_section("trigger-referral", "triggers.trigger_create_referral", "icon-exit")

        #PE-207: hide ticket feature
        #add_section("trigger-closed-ticket", "triggers.trigger_create_closed_ticket", "icon-ticket")
    #enddef derive_formax_sections

#endclass TriggerCreateOverrides
