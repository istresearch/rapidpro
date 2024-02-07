import logging
import requests

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from rest_framework.views import View

from temba.channels.models import Channel
from temba.orgs.models import Org
from temba.orgs.views import OrgPermsMixin
from temba.utils import json

from engage.utils import get_required_arg
from engage.utils.logs import OrgPermLogInfoMixin


class PurgeOutboxMixin:

    @classmethod
    def get_actions(cls):
        return (
            "purge_outbox",
        )
    #enddef get_actions

    class PurgeOutbox(OrgPermLogInfoMixin, OrgPermsMixin, View):  # pragma: no cover
        permission = "msgs.broadcast_send"

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r"^%s/(?P<channel_type>[^/]+)/(?P<channel_uuid>[^/]+)/$" % ('purge',)
        #enddef derive_url_pattern

        def postCourierPurgeReqest(self, aBaseCourierURL, aChannelType, aChannelUUID):
            logger = logging.getLogger()
            theEndpoint = f"{aBaseCourierURL}/purge/{aChannelType}/{aChannelUUID}"
            logger.info("purge outbox started", extra=self.withLogInfo({
                'channel_type': aChannelType,
                'channel_uuid': aChannelUUID,
            }))
            try:
                r = requests.post(theEndpoint, headers={"Content-Type": "application/json"})
                theMessage = json.loads(r.content)['message']
                logger.info(f"purge outbox returned {r.status_code}", extra=self.withLogInfo({
                    'channel_type': aChannelType,
                    'channel_uuid': aChannelUUID,
                    'status_code': r.status_code,
                    'courier_response': theMessage,
                }))
                return HttpResponse(f"The courier service returned with status {r.status_code}: {theMessage}")
            except ConnectionError as ex:
                logger.error("purge outbox cannot reach courier", extra=self.withLogInfo({
                    'channel_type': aChannelType,
                    'channel_uuid': aChannelUUID,
                    'courier_url': aBaseCourierURL,
                }))
                return HttpResponse("A fatal error has occurred, action may not have fully finished.", status=500)
            #endtry
        #enddef

        def dispatch(self, request: HttpRequest, *args, **kwargs):
            # non authenticated users without orgs get an error (not the org chooser)
            user = self.get_user()
            if not user.is_authenticated:
                return HttpResponse('Not authorized', status=401)

            return super().dispatch(request, *args, **kwargs)
        #enddef dispatch

        def get(self, request: HttpRequest, *args, **kwargs):
            logger = logging.getLogger()

            user = self.get_user()
            if not user.get_org():
                theOrgPK = request.GET.get('org')
                if theOrgPK:
                    org = Org.objects.filter(id=theOrgPK).first()
                    if org is not None:
                        user.set_org(org)
                if not user.get_org():
                    return HttpResponse('Org ambiguous, please specify', status=400)

            if not user.is_allowed(self.permission):
                return HttpResponse('Forbidden', status=403)

            # ensure we have the necessary args
            try:
                theChannelType = get_required_arg('channel_type', kwargs)
                theChannelUUID = get_required_arg('channel_uuid', kwargs)
                theBaseCourierURL = settings.COURIER_URL
                #logger.debug(f"Courier URL=[{theBaseCourierURL}]")
                if theBaseCourierURL is not None and len(theBaseCourierURL) > 0:
                    theBaseCourierURL = theBaseCourierURL.rstrip('/')
                else:
                    logger.error("purge outbox malformed Courier URL", extra=self.withLogInfo({
                        'channel_type': theChannelType,
                        'channel_uuid': theChannelUUID,
                    }))
                    raise ValueError("Courier URL malformed")
            except ValueError as vx:
                return HttpResponse(vx, status=400)

            if theChannelType == '4org':
                org = user.get_org()
                if theChannelUUID.replace('-', '') == org.uuid.hex:
                    theOverallRespMsg = 'All channels for this org have started purging themselves.'
                    theOverallRespStatus = 200
                    theChannelList = Channel.objects.filter(org_id=org.id, is_active=True).order_by('last_seen')
                    for theChannel in theChannelList:
                        resp = self.postCourierPurgeReqest(theBaseCourierURL, theChannel.type, theChannel.uuid)
                        if resp.status_code < 200 or resp.status_code > 299:
                            theOverallRespStatus = 500
                            theOverallRespMsg += "\nError Report: "+resp.content
                        #endif
                    #endfor
                    return HttpResponse(theOverallRespMsg, status=theOverallRespStatus)
                else:
                    return HttpResponse('Org ambiguous, please rectify', status=400)
                #endif
            else:
                return self.postCourierPurgeReqest(theBaseCourierURL, theChannelType, theChannelUUID)
            #endif
        #enddef get

        def post(self, request, *args, **kwargs):
            return HttpResponse("METHOD not allowed", status=405)
        #enddef post
