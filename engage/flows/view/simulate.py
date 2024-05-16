from django.conf import settings
from django.http import JsonResponse

from engage.utils.class_overrides import MonkeyPatcher

from temba import mailroom
from temba.channels.models import Channel
from temba.flows.models import Flow
from temba.flows.views import FlowCRUDL
from temba.utils import json, analytics


class FlowViewSimulate(MonkeyPatcher):
    patch_class = FlowCRUDL.Simulate

    def post(self, request, *args, **kwargs):
        try:
            json_dict = json.loads(request.body)
        except Exception as e:  # pragma: needs cover
            return JsonResponse(dict(status="error", description="Error parsing JSON: %s" % str(e)), status=400)
        #endtry

        if not settings.MAILROOM_URL:  # pragma: no cover
            return JsonResponse(
                dict(status="error", description="mailroom not configured, cannot simulate"), status=500
            )
        #endif

        flow = self.get_object()
        client = mailroom.get_client()

        analytics.track(request.user, "temba.flow_simulated", dict(flow=flow.name, uuid=flow.uuid))

        simChan = Channel.SIMULATOR_CHANNEL
        simChan['roles'] = ["send", "receive", "call"]
        simChan['country'] = "US"
        chanFilter = flow.metadata.get('channels', [])
        if len(chanFilter) > 0:
            # if flow limits what channels it can use, ensure simulator uuid is one of them
            channel_uuid = chanFilter[0]
        #endif
        channel_uuid = simChan['uuid']
        channel_name = simChan['name']

        # build our request body, which includes any assets that mailroom should fake
        payload = {
            "org_id": flow.org_id,
            "assets": {
                "channels": [simChan],
            },
        }

        if "flow" in json_dict:
            payload["flows"] = [{
                "uuid": flow.uuid,
                "definition": json_dict["flow"],
            }]
        #endif

        # check if we are triggering a new session
        if "trigger" in json_dict:
            payload["trigger"] = json_dict["trigger"]

            # ivr flows need a connection in their trigger
            if flow.flow_type == Flow.TYPE_VOICE:
                payload["trigger"]["connection"] = {
                    "channel": {"uuid": channel_uuid, "name": channel_name},
                    "urn": "tel:+12065551212",
                }
            #endif

            payload["trigger"]["environment"] = flow.org.as_environment_def()
            payload["trigger"]["user"] = self.request.user.as_engine_ref()

            try:
                return JsonResponse(client.sim_start(payload))
            except mailroom.MailroomException:
                return JsonResponse(dict(status="error", description="mailroom error"), status=500)
            #endtry

        # otherwise we are resuming
        elif "resume" in json_dict:
            payload["resume"] = json_dict["resume"]
            payload["resume"]["environment"] = flow.org.as_environment_def()
            payload["session"] = json_dict["session"]

            try:
                return JsonResponse(client.sim_resume(payload))
            except mailroom.MailroomException:
                return JsonResponse(dict(status="error", description="mailroom error"), status=500)
            #endtry
        #endif
    #enddef post

#endclass FlowViewSimulate
