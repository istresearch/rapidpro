import json
import logging

from django.http import HttpRequest, HttpResponse
from django.views import View

from engage.api.exceptions import ValueException
from engage.utils import get_required_arg
from engage.utils.logs import OrgPermLogInfoMixin
from temba.channels.models import Channel
from temba.orgs.views import OrgPermsMixin


class PmRenameChannels(OrgPermLogInfoMixin, OrgPermsMixin, View):  # pragma: no cover
    permission = "channels.channel_update"

    @classmethod
    def derive_url_pattern(cls, path, action):
        return r"^%s/%s/(?P<channel_id>[^/]+)/$" % (path, action)
    #enddef derive_url_pattern

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        # non authenticated users without orgs get an error (not the org chooser)
        user = self.get_user()
        if not user.is_authenticated:
            return HttpResponse('Not authorized', status=401)
        #endif
        return super().dispatch(request, *args, **kwargs)
    #enddef dispatch

    def get(self, request: HttpRequest, *args, **kwargs):
        return HttpResponse("METHOD not allowed", status=405)
    #enddef get

    def post(self, request: HttpRequest, *args, **kwargs):
        logger = logging.getLogger()
        reqData = request.POST

        # ensure we have the necessary args
        try:
            channel_id: str = get_required_arg('channel_id', kwargs)
            name_format: str = reqData.get('name_format')
            if not name_format:
                raise ValueException.withCause(cause='missing argument', msg=f"[{name_format}] not defined.")
            #endif
        except ValueError as vx:
            return HttpResponse(vx, status=400)
        #endtry

        theParentChannel: Channel = Channel.objects.filter(pk=channel_id).first() \
            if channel_id.isdigit() else Channel.objects.filter(uuid=channel_id).first()

        if theParentChannel:
            user = self.get_user()
            if not user.get_org():
                user.set_org(theParentChannel.org)
            #endif
            if not user.is_allowed(self.permission):
                return HttpResponse('Forbidden', status=403)
            #endif allowed

            #ensure we have a default in case blank is passed in
            if not name_format:
                name_format = '{{phone_number}} [{{pm_scheme}}]'
            #endif
            #ensure we have something channel-specific so they don't end up all with same name
            if name_format.find('{{pm_scheme}}') < 0 and name_format.find('{{pm_mode}}') < 0:
                name_format += ' [{{pm_scheme}}]'
            #endif
            theParentChannel.config['name_format'] = name_format
            old_name = theParentChannel.name
            theParentChannel.name = Channel.formatChannelName(name_format, theParentChannel, user)
            theParentChannel.save(update_fields=['config', 'name'])
            logger.info('channel renamed', extra=self.withLogInfo({
                'channel_pk': theParentChannel.id,
                'channel_uuid': theParentChannel.uuid,
                'device_id': theParentChannel.address,
                'old_name': old_name,
                'new_name': theParentChannel.name,
            }))

            theChannelList = Channel.objects.filter(is_active=True, parent_id=theParentChannel.id)
            for theChildChannel in theChannelList:
                old_name = theChildChannel.name
                theChildChannel.name = Channel.formatChannelName(name_format, theChildChannel, user)
                theChildChannel.save(update_fields=['name'])
                logger.info('channel renamed', extra=self.withLogInfo({
                    'channel_pk': theChildChannel.id,
                    'channel_uuid': theChildChannel.uuid,
                    'device_id': theChildChannel.address,
                    'old_name': old_name,
                    'new_name': theChildChannel.name,
                }))
            #endfor
            return HttpResponse(json.dumps({
                'msg': f'All channels for device "{theParentChannel.address}" renamed',
                'id': theParentChannel.id,
                'name': theParentChannel.name,
            }), content_type='application/json')
        else:
            return HttpResponse(json.dumps({
                'msg': "Unknown device",
            }), content_type='application/json', status=422)
        #endif
    #enddef post

#endclass PmRenameChannels
