import logging
import requests

from django.http import HttpRequest, HttpResponse
from rest_framework.views import View

from temba import settings
from temba.orgs.models import Org
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

        def dispatch(self, request: HttpRequest, *args, **kwargs):
            # non authenticated users without orgs get an error (not the org chooser)
            user = self.get_user()
            if not user.is_authenticated:
                return HttpResponse('Not authorized', status=401)

            if user.is_authenticated and not user.derive_org():
                theOrgPK = request.GET.get('org')
                if theOrgPK:
                    org = Org.objects.filter(id=theOrgPK).first()
                    if org is not None:
                        user.set_org(org)
                if not user.derive_org():
                    return HttpResponse('Org ambiguous, please specify', status=400)

            if not user.has_org_perm(self.permission):
                return HttpResponse('Forbidden', status=403)

            return super().dispatch(request, *args, **kwargs)

        def get(self, request, *args, **kwargs):
            logger = logging.getLogger(__name__)

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
                    'message': theMessage,
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
