import logging
import requests

from django.http import HttpRequest, HttpResponse
from rest_framework.views import View

from temba import settings
from temba.orgs.models import Org
from temba.orgs.views import OrgPermsMixin
from temba.utils import json

from engage.auth.account import UserAcct
from engage.utils import get_required_arg
from engage.utils.logs import OrgPermLogInfoMixin


class PurgeOutboxMixin:

    @classmethod
    def get_actions(cls):
        return (
            "purge_outbox",
        )

    class PurgeOutbox(OrgPermLogInfoMixin, OrgPermsMixin, View):  # pragma: no cover
        permission = "msgs.broadcast_send"

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r"^%s/(?P<channel_type>[^/]+)/(?P<channel_uuid>[^/]+)/$" % ('purge')

        def dispatch(self, request: HttpRequest, *args, **kwargs):
            # non authenticated users without orgs get an error (not the org chooser)
            user = self.get_user()
            if not user.is_authenticated:
                return HttpResponse('Not authorized', status=401)

            return super().dispatch(request, *args, **kwargs)

        def get(self, request: HttpRequest, *args, **kwargs):
            logger = logging.getLogger(__name__)

            user = self.get_user()
            if not UserAcct.get_org(user):
                theOrgPK = request.GET.get('org')
                if theOrgPK:
                    org = Org.objects.filter(id=theOrgPK).first()
                    if org is not None:
                        UserAcct.set_org(user, org)
                if not UserAcct.get_org(user):
                    return HttpResponse('Org ambiguous, please specify', status=400)

            if not UserAcct.is_allowed(user, self.permission):
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

            theEndpoint = f"{theBaseCourierURL}/purge/{theChannelType}/{theChannelUUID}"
            logger.info("purge outbox started", extra=self.withLogInfo({
                'channel_type': theChannelType,
                'channel_uuid': theChannelUUID,
            }))
            try:
                r = requests.post(theEndpoint, headers={"Content-Type": "application/json"})
                theMessage = json.loads(r.content)['message']
                logger.info(f"purge outbox returned {r.status_code}", extra=self.withLogInfo({
                    'channel_type': theChannelType,
                    'channel_uuid': theChannelUUID,
                    'status_code': r.status_code,
                    'courier_response': theMessage,
                }))
                return HttpResponse(f"The courier service returned with status {r.status_code}: {theMessage}")
            except ConnectionError as ex:
                logger.error("purge outbox cannot reach courier", extra=self.withLogInfo({
                    'channel_type': theChannelType,
                    'channel_uuid': theChannelUUID,
                    'courier_url': theBaseCourierURL,
                }))
                return HttpResponse("A fatal error has occured, action may not have fully finished.", status=500)

        def post(self, request, *args, **kwargs):
            return HttpResponse("METHOD not allowed", status=405)
