from collections import defaultdict

from django.conf import settings
from django.contrib import messages
from django.urls import reverse

from .manage import ManageChannelMixin
from .purge_outbox import PurgeOutboxMixin
from .types.postmaster.apks import APIsForDownloadPostmaster

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.channels.models import Channel
from temba.channels.types.postmaster.type import PostmasterType
from temba.channels.views import ChannelCRUDL


class ChannelCRUDLOverrides(ClassOverrideMixinMustBeFirst, ManageChannelMixin,
                            PurgeOutboxMixin, APIsForDownloadPostmaster, ChannelCRUDL):
    override_ignore = ('get_actions',)

    @staticmethod
    def on_apply_overrides(under_cls):
        under_cls.actions += \
           ManageChannelMixin.get_actions() + \
           PurgeOutboxMixin.get_actions() + \
           APIsForDownloadPostmaster.get_actions()
    #enddef on_apply_overrides

#endclass ChannelCRUDLOverrides


class ChannelReadOverrides(ClassOverrideMixinMustBeFirst, ChannelCRUDL.Read):

    def get_gear_links(self):
        links = self.getOrigClsAttr('get_gear_links')(self)

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

#endclass ChannelReadOverrides


class ChannelClaimOverrides(ClassOverrideMixinMustBeFirst, ChannelCRUDL.Claim):

    def channel_types_groups(self):
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
        context = self.orig_get_context_data(**kwargs)
        # engage features a single channel
        context["featured_channel"] = Channel.get_type_from_code(PostmasterType.code)
        return context
    #enddef get_context_data

#endclass ChannelClaimOverrides


class ChannelClaimAllOverrides(ClassOverrideMixinMustBeFirst, ChannelCRUDL.ClaimAll):

    def channel_types_groups(self):
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


class ChannelDeleteOverrides(ClassOverrideMixinMustBeFirst, ChannelCRUDL.Delete):

    def get_success_url(self):
        # if we're deleting a child channel, redirect to parent afterwards
        channel = self.get_object()
        if channel.parent:
            return reverse("channels.channel_read", args=[channel.parent.uuid])

        return reverse("channels.channel_manage")
    #enddef get_success_url

    def post(self, request, *args, **kwargs):
        try:
            return self.getOrigClsAttr('post')(self, request=request, *args, **kwargs)
        except ValueError as vex:
            messages.error(request, vex)
            from django.http import HttpResponse
            return HttpResponse(
                vex,
                headers={
                    "Temba-Success": self.cancel_url,
                },
                status=204,
            )
        #endtry
    #enddef post

#endclass ChannelDeleteOverrides

class ChannelUpdateOverrides(ClassOverrideMixinMustBeFirst, ChannelCRUDL.Update):

    def pre_save(self, obj):
        obj = self.getOrigClsAttr('pre_save')(self, obj)
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

class ChannelListOverrides(ClassOverrideMixinMustBeFirst, ChannelCRUDL.List):
    link_url = 'uuid@channels.channel_read'

    def get_queryset(self, **kwargs):
        queryset = self.getOrigClsAttr('get_queryset')(self, **kwargs)

        req = self.request
        if req and req.user and req.user.is_superuser and not req.GET.get("showall"):
            queryset = queryset.filter(org__isnull=False)
        #endif

        return queryset
    #enddef get_queryset

#endclass ChannelListOverrides
