import logging
import requests

from django.http import HttpResponse
from rest_framework.views import View

from temba import settings
from temba.orgs.views import OrgPermsMixin
from temba.utils import json

from engage.utils import get_required_arg
from engage.utils.logs import OrgPermLogInfoMixin


class PurgeOutboxMixin:

    class PurgeOutbox(OrgPermLogInfoMixin, OrgPermsMixin, View):  # pragma: no cover
        permission = "msgs.broadcast_send"

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r"^%s/(?P<channel_type>[^/]+)/(?P<channel_uuid>[^/]+)/$" % ('purge')

        def get(self, request, *args, **kwargs):
            logger = logging.getLogger(__name__)

            # ensure we have a logged in user with the correct permission(s)
            theUser = self.get_user()
            if theUser is None or not (theUser.is_authenticated and not theUser.is_anonymous):
                return HttpResponse('Not authorized', status=401)
            self.org = self.derive_org()
            if not self.org or not self.has_org_perm(self.permission):
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
                logger.info("purge outbox returned 200", extra=self.withLogInfo({
                    'channel_type': theChannelType,
                    'channel_uuid': theChannelUUID,
                }))
                return HttpResponse(f"The courier service returned with status {r.status_code}: {json.loads(r.content)['message']}")
            except ConnectionError as ex:
                logger.error("purge outbox cannot reach courier", extra=self.withLogInfo({
                    'channel_type': theChannelType,
                    'channel_uuid': theChannelUUID,
                    'courier_url': theBaseCourierURL,
                }))
                return HttpResponse("A fatal error has occured, action may not have fully finished.", status=500)

        def post(self, request, *args, **kwargs):
            return HttpResponse("METHOD not allowed", status=405)
