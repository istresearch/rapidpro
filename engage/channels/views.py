from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from twilio.base.exceptions import TwilioRestException

from .manage import ManageChannelMixin
from .purge_outbox import PurgeOutboxMixin
from .types.postmaster.apks import APIsForDownloadPostmaster

from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.middleware import RedirectTo

from temba.channels.models import Channel
from temba.channels.types.postmaster.type import PostmasterType
from temba.channels.views import ChannelCRUDL


class ChannelCRUDLOverrides(MonkeyPatcher, ManageChannelMixin,
                            PurgeOutboxMixin, APIsForDownloadPostmaster):
    patch_class = ChannelCRUDL
    patch_ignore = ('get_actions',)

    @staticmethod
    def on_apply_patches(under_cls):
        under_cls.actions += \
           ManageChannelMixin.get_actions() + \
           PurgeOutboxMixin.get_actions() + \
           APIsForDownloadPostmaster.get_actions()
    #enddef on_apply_patches

#endclass ChannelCRUDLOverrides


class ChannelReadOverrides(MonkeyPatcher):
    patch_class = ChannelCRUDL.Read

    def get_gear_links(self):
        links = self.super_get_gear_links()

        # as_btn introduced to determine if placed in hamburger menu or as its own button
        el = [x for x in links if hasattr(x, 'id') and x.id == 'update-channel']
        if el:
            el.as_btn = True

        # append the Purge Outbox link as a button
        links.append(
            dict(
                id="action-purge",
                title="Purge Outbox",
                as_btn=True,
                js_class="button-danger",
            )
        )

        return links
    #enddef get_gear_links

    def has_permission(self: ChannelCRUDL.Read, request, *args, **kwargs):
        user = self.get_user()
        # if user has permission to the org this channel resides, just switch the org for them
        obj_org = self.get_object_org()
        if user.has_org_perm(obj_org, self.permission):
            if obj_org.pk != user.get_org().pk:
                user.set_org(obj_org)
                request.session["org_id"] = obj_org.pk
                raise RedirectTo(request.build_absolute_uri())
            #endif
            return True
        else:
            return False
        #endif
    #enddef

#endclass ChannelReadOverrides


class ChannelClaimOverrides(MonkeyPatcher):
    patch_class = ChannelCRUDL.Claim

    def channel_types_groups(self: ChannelCRUDL.Claim):
        user = self.request.user

        # fetch channel types, sorted by category and name
        types_by_category = defaultdict(list)
        recommended_channels = []
        for ch_type in list(Channel.get_types()):
            region_aware_visible, region_ignore_visible = ch_type.is_available_to(user)

            if ch_type.is_recommended_to(user):
                recommended_channels.append(ch_type)
            #elif region_ignore_visible and region_aware_visible and ch_type.category:
            # recommended channels _duplicated_, not either/or listings
            if region_ignore_visible and region_aware_visible and ch_type.category:
                types_by_category[ch_type.category.name].append(ch_type)

        return recommended_channels, types_by_category, True
    #enddef channel_types_groups

    def get_context_data(self, **kwargs):
        context = self.super_get_context_data(**kwargs)
        # engage features a single channel
        context["featured_channel"] = Channel.get_type_from_code(PostmasterType.code)
        return context
    #enddef get_context_data

#endclass ChannelClaimOverrides


class ChannelClaimAllOverrides(MonkeyPatcher):
    patch_class = ChannelCRUDL.ClaimAll

    def channel_types_groups(self: ChannelCRUDL.ClaimAll):
        user = self.request.user

        types_by_category = defaultdict(list)
        recommended_channels = []
        for ch_type in list(Channel.get_types()):
            region_aware_visible, region_ignore_visible = ch_type.is_available_to(user)
            if ch_type.is_recommended_to(user):
                recommended_channels.append(ch_type)
            #elif region_ignore_visible and ch_type.category:
            # recommended channels _duplicated_, not either/or listings
            if region_ignore_visible and ch_type.category:
                types_by_category[ch_type.category.name].append(ch_type)

        return recommended_channels, types_by_category, False
    #enddef channel_types_groups

#endclass ChannelClaimAllOverrides


class ChannelDeleteOverrides(MonkeyPatcher):
    patch_class = ChannelCRUDL.Delete

    def get_success_url(self: ChannelCRUDL.Delete):
        # if we're deleting a child channel, redirect to parent afterwards
        channel = self.get_object()
        if channel.parent:
            return reverse("channels.channel_read", args=[channel.parent.uuid])

        return reverse("channels.channel_manage")
    #enddef get_success_url

    def post(self: ChannelCRUDL.Delete, request, *args, **kwargs):
        channel = self.get_object()

        try:
            channel.release(request.user, check_dependent_flows=False)
        except TwilioRestException as e:
            messages.error(
                request,
                _(
                    f"Twilio reported an error removing your channel (error code {e.code}). Please try again later."
                ),
            )

            response = HttpResponse()
            response["Temba-Success"] = self.cancel_url
            return response

        # override success message for Twilio channels
        if channel.channel_type == "T" and not channel.is_delegate_sender():
            messages.info(request, self.success_message_twilio)
        else:
            messages.info(request, self.success_message)

        response = HttpResponse()
        response["Temba-Success"] = self.get_success_url()
        return response
        #endtry
    #enddef post

#endclass ChannelDeleteOverrides

class ChannelUpdateOverrides(MonkeyPatcher):
    patch_class = ChannelCRUDL.Update

    def pre_save(self, obj):
        obj = self.super_pre_save(obj)
        if hasattr(obj, 'tps'):
            max_tps = getattr(settings, "MAX_TPS", 50)
            def_tps = getattr(settings, "DEFAULT_TPS", 10)
            if obj.tps is None:
                obj.tps = def_tps
            elif obj.tps <= 0:
                obj.tps = def_tps
            elif obj.tps > max_tps:
                obj.tps = max_tps
            #endif
        #endif obj.tps
        return obj
    #enddef pre_save

#endclass ChannelUpdateOverrides

class ChannelListOverrides(MonkeyPatcher):
    patch_class = ChannelCRUDL.List
    link_url = 'uuid@channels.channel_read'

    def get_queryset(self: ChannelCRUDL.List, **kwargs):
        queryset = self.super_get_queryset(**kwargs)

        req = self.request
        if req and req.user and req.user.is_superuser and not req.GET.get("showall"):
            queryset = queryset.filter(org__isnull=False)
        #endif

        return queryset
    #enddef get_queryset

#endclass ChannelListOverrides
