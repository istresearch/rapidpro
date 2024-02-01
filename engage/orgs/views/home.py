from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from temba.channels.models import Channel
from temba.orgs.models import IntegrationType
from temba.orgs.views import OrgCRUDL, SmartReadView

from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.logs import LogExtrasMixin


class HomeOverrides(MonkeyPatcher, LogExtrasMixin):
    patch_class = OrgCRUDL.Home

    def get_gear_links(self: type(OrgCRUDL.Home)):
        links = []

        if self.has_org_perm("orgs.org_manage_accounts"):
            links.append(dict(title=_("Assign User"), href=reverse("orgs.org_assign_user")))

        if self.has_org_perm("channels.channel_configuration"):
            links.append(dict(title=_("Manage Channels"), href=reverse("channels.channel_manage"), as_btn=True))

        #call original overridden function, not super(), so we don't have to re-write it here.
        links.extend(self.super_get_gear_links())

        #PE-207: hide ticket feature
        theAddTicketSvc = reverse("tickets.ticketer_connect")
        links[:] = [item for item in links if ('href' in item and item['href'] == theAddTicketSvc)]

        theAddChannelUrl = reverse("channels.channel_claim")
        for item in links:
            if item['href'] == theAddChannelUrl:
                item['as_btn'] = True
                break
            #endif
        #endfor each link item

        return links
    #enddef get_gear_links

    def get_context_data(self, *args, **kwargs):
        context = super(OrgCRUDL.Home, self).get_context_data(*args, **kwargs)
        # we skip calling super_get_context_data because we don't want the super slow "channels" context.
        org = self.request.user.get_org()
        if org and org.config:
            context['mauth_enabled'] = org.config.get('mauth_enabled', 0)
        #endif
        return context
    #enddef get_context_data

    def derive_formax_sections(self: type(OrgCRUDL.Home), formax, context):
        # add the channel option if we have one
        user = self.request.user
        org = user.get_org()

        # if we are on the topups plan, show our usual credits view
        if org.plan == settings.ORG_PLAN_TOPUP:
            if self.has_org_perm("orgs.topup_list"):
                formax.add_section("topups", reverse("orgs.topup_list"), icon="icon-coins", action="link")

        else:
            if self.has_org_perm("orgs.org_plan"):  # pragma: needs cover
                formax.add_section("plan", reverse("orgs.org_plan"), icon="icon-credit", action="summary")

        if self.has_org_perm("channels.channel_update"):
            # Removed due to slow load time when channel count greater than 5
            # get any channel that is not a delegate
            # channels = Channel.objects.filter(org=org, is_active=True, parent=None).order_by("-role")
            # for channel in channels:
            #     self.add_channel_section(formax, channel)
            # endfor each channel

            # Removed due to excess load time
            twilio_client = org.get_twilio_client()
            if twilio_client:  # pragma: needs cover
                formax.add_section("twilio", reverse("orgs.org_twilio_account"), icon="icon-channel-twilio")
            #endif twilio

            # Removed due to excess load time
            vonage_client = org.get_vonage_client()
            if vonage_client:  # pragma: needs cover
                formax.add_section("vonage", reverse("orgs.org_vonage_account"), icon="icon-vonage")
            #endif vonage

            # Removed due to not supporting BWI anymore
            #try:
            #    from temba.channels.types.bandwidth_international import BandwidthInternationalType
            #    if Channel.get_type_from_code(BandwidthInternationalType.code) is not None:
            #        bwi_client = org.get_bandwidth_international_messaging_client()
            #        if bwi_client:
            #            formax.add_section("BWI", reverse("orgs.org_bandwidth_international_account"),
            #                               icon="icon-tembatoo-bandwidth")
            #except ValueError:
            #    pass
            #endtry bandwidth intl client

            try:
                from temba.channels.types.bandwidth import BandwidthType
                if Channel.get_type_from_code(BandwidthType.code) is not None:
                    bwd_client = org.get_bandwidth_messaging_client()
                    if bwd_client:
                        formax.add_section("BWD", reverse("orgs.org_bandwidth_account"),
                                           icon="icon-tembatoo-bandwidth")
            except ValueError:
                pass
            #endtry bandwidth domestic client
        #endif can update channels

        if self.has_org_perm("classifiers.classifier_read"):
            classifiers = org.classifiers.filter(is_active=True).order_by("created_on")
            for classifier in classifiers:
                self.add_classifier_section(formax, classifier)

        if self.has_org_perm("tickets.ticketer_read"):
            from temba.tickets.types.internal import InternalType

            ext_ticketers = (
                org.ticketers.filter(is_active=True)
                    .exclude(ticketer_type=InternalType.slug)
                    .order_by("created_on")
            )
            for ticketer in ext_ticketers:
                formax.add_section(
                    "tickets",
                    reverse("tickets.ticketer_read", args=[ticketer.uuid]),
                    icon=ticketer.get_type().icon,
                )

        if self.has_org_perm("orgs.org_profile"):
            formax.add_section("user", reverse("orgs.user_edit"), icon="icon-user", action="redirect")

        if self.has_org_perm("orgs.org_two_factor"):
            if user.settings.two_factor_enabled:
                formax.add_section(
                    "two_factor", reverse("orgs.user_two_factor_tokens"), icon="icon-two-factor", action="link"
                )
            else:
                formax.add_section(
                    "two_factor", reverse("orgs.user_two_factor_enable"), icon="icon-two-factor", action="link"
                )

        if self.has_org_perm("orgs.org_edit"):
            formax.add_section(
                'mauth_required', reverse('orgs.org_mutual_auth_config'), icon='icon-two-factor',
            )
        #endif

        if self.has_org_perm("orgs.org_edit"):
            formax.add_section("org", reverse("orgs.org_edit"), icon="icon-office")

        # only pro orgs get multiple users
        if self.has_org_perm("orgs.org_manage_accounts") and org.is_multi_user:
            formax.add_section("accounts", reverse("orgs.org_accounts"), icon="icon-users", action="redirect")

        if self.has_org_perm("orgs.org_languages"):
            formax.add_section("languages", reverse("orgs.org_languages"), icon="icon-language")

        if self.has_org_perm("orgs.org_country"):
            formax.add_section("country", reverse("orgs.org_country"), icon="icon-location2")

        if self.has_org_perm("orgs.org_smtp_server"):
            formax.add_section("email", reverse("orgs.org_smtp_server"), icon="icon-envelop")

        if self.has_org_perm("orgs.org_manage_integrations"):
            for integration in IntegrationType.get_all():
                if integration.is_available_to(user):
                    integration.management_ui(self.object, formax)

        if self.has_org_perm("orgs.org_token"):
            formax.add_section("token", reverse("orgs.org_token"), icon="icon-cloud-upload", nobutton=True)

        if self.has_org_perm("orgs.org_prometheus"):
            formax.add_section("prometheus", reverse("orgs.org_prometheus"), icon="icon-prometheus", nobutton=True)

        if self.has_org_perm("orgs.org_resthooks"):
            formax.add_section(
                "resthooks", reverse("orgs.org_resthooks"), icon="icon-cloud-lightning", dependents="resthooks"
            )

        # show globals and archives
        formax.add_section("globals", reverse("globals.global_list"), icon="icon-global", action="link")
        formax.add_section("archives", reverse("archives.archive_message"), icon="icon-box", action="link")
    #enddef derive_formax_sections

#endclass HomeOverrides
