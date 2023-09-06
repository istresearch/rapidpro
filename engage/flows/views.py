from datetime import timedelta
import logging

from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from smartmin.views import SmartUpdateView

from temba.mailroom import FlowValidationException
from temba.orgs.views import OrgObjPermsMixin
from temba.utils import analytics, json
from temba.utils.s3 import public_file_storage
from temba.utils.uuid import uuid4
from temba.utils.views import NonAtomicMixin
from temba.flows.models import (
    FlowUserConflictException,
    FlowVersionConflictException,
)
from temba.flows.views import FlowCRUDL


logger = logging.getLogger()

class FlowCRUDLOverrides(ClassOverrideMixinMustBeFirst, FlowCRUDL):

    class Json(NonAtomicMixin, FlowCRUDL.AllowOnlyActiveFlowMixin, OrgObjPermsMixin, SmartUpdateView):
        slug_url_kwarg = "uuid"
        success_message = ""

        def get(self, request, *args, **kwargs):
            flow = self.get_object()
            flow.ensure_current_version()

            # all the translation languages for our org
            languages = [lang.as_json() for lang in flow.org.languages.all().order_by("orgs")]

            # all countries we have a channel for, never fail here
            try:
                channel_countries = flow.org.get_channel_countries()
            except Exception:  # pragma: needs cover
                logger.error("Unable to get currency for channel countries.", exc_info=True)
                channel_countries = []

            # all the channels available for our org
            channels = [
                dict(uuid=chan.uuid, name=f"{chan.get_channel_type_display()}: {chan.name + (' (Last seen: ' + str(chan.last_seen.strftime('%Y-%m-%d %H:%M %Z)')) if chan.channel_type == 'PSM' else '')}")
                for chan in flow.org.channels.filter(is_active=True)
            ]
            return JsonResponse(
                dict(
                    flow=flow.as_json(expand_contacts=True),
                    languages=languages,
                    channel_countries=channel_countries,
                    channels=channels,
                )
            )
        #enddef get

        def post(self, request, *args, **kwargs):
            # require update permissions
            if not self.has_org_perm("flows.flow_update"):
                return HttpResponseRedirect(reverse("flows.flow_json", args=[self.get_object().pk]))

            # try to parse our body
            json_string = force_str(request.body)

            # if the last modified on this flow is more than a day ago, log that this flow as updated
            if self.get_object().saved_on < timezone.now() - timedelta(hours=24):  # pragma: needs cover
                analytics.track(self.request.user, "temba.flow_updated")

            # try to save the flow, if this fails, let's let that bubble up to our logger
            json_dict = json.loads(json_string)
            print(json.dumps(json_dict, indent=2))

            try:
                flow = self.get_object(self.get_queryset())
                revision = flow.update(json_dict, user=self.request.user)
                return JsonResponse(
                    {
                        "status": "success",
                        "saved_on": json.encode_datetime(flow.saved_on, micros=True),
                        "revision": revision.revision,
                    },
                    status=200,
                )

            except FlowValidationException:  # pragma: no cover
                error = _("Your flow failed validation. Please refresh your browser.")
            except FlowVersionConflictException:
                error = _(
                    "Your flow has been upgraded to the latest version. "
                    "In order to continue editing, please refresh your browser."
                )
            except FlowUserConflictException as e:
                error = (
                    _(
                        "%s is currently editing this Flow. "
                        "Your changes will not be saved until you refresh your browser."
                    )
                    % e.other_user
                )
            except Exception:  # pragma: no cover
                error = _("Your flow could not be saved. Please refresh your browser.")

            return JsonResponse({"status": "failure", "description": error}, status=400)
        #enddef post

    #endclass Json

#endclass FlowCRUDLOverrides

class ArchivedViewOverrides(ClassOverrideMixinMustBeFirst, FlowCRUDL.Archived):
    bulk_action_permissions = {"delete": "flows.flow_delete"}

    def get_bulk_actions(self):
        actions = []
        if self.has_org_perm("flows.flow_update"):
            actions.append("restore")
        #endif
        if self.has_org_perm("flows.flow_delete"):
            actions.append("delete")
        #endif
        return actions
    #enddef get_bulk_actions

    def apply_bulk_action(self, user, action, objects, label):
        self.apply_bulk_action_toast = None
        if action == "delete":
            num_obj = len(objects)
            self.super_apply_bulk_action(user, action, objects, label)
            if num_obj > 1:
                self.apply_bulk_action_toast = f"All {num_obj} flows deleted"
            #endif
        else:
            self.super_apply_bulk_action(user, action, objects, label)
        #endif
    #enddef apply_bulk_action

#endclass ArchivedViewOverrides

class UploadMediaActionOverrides(ClassOverrideMixinMustBeFirst, FlowCRUDL.UploadMediaAction):
    # bugfix: respect STORAGE_URL

    def save_media_upload(self, file):
        flow = self.get_object()

        # browsers might send m4a files but correct MIME type is audio/mp4
        extension = file.name.split(".")[-1]
        if extension == "m4a":
            file.content_type = "audio/mp4"

        path = f"attachments/{flow.org.id}/{flow.id}/steps/{str(uuid4())}/{file.name}"
        path = public_file_storage.save(path, file)  # storage classes can rewrite saved paths

        return {"type": file.content_type, "url": f"{settings.STORAGE_URL}/{path}"}
    #enddef save_media_upload

#endclass UploadMediaActionOverrides
