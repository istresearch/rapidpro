import logging

from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import MonkeyPatcher

from temba.flows.models import Flow


class FlowOverrides(MonkeyPatcher):
    patch_class = Flow

    TYPE_CHOICES = (
        (Flow.TYPE_MESSAGE, _("Messaging")),
        (Flow.TYPE_VOICE, _("Phone Call")),
        (Flow.TYPE_BACKGROUND, _("Background")),
        # (Flow.TYPE_SURVEY, _("Surveyor")), # P4-1483
    )

    @classmethod
    def apply_action_delete(cls, user, flows):
        logger = logging.getLogger()
        org = user.get_org()
        for flow in flows:
            try:
                logger.info("delete flow", extra={
                    'flow_id': flow.pk,
                    'flow_name': flow.name,
                    'flow_uuid': flow.uuid,
                    'user': user.email,
                    'org_id': org.id,
                    'org_name': org.name,
                    'org_uuid': org.uuid,
                })
                flow.release(user)
            except Exception as ex:
                # not a code error, so using log warning
                logger.warning("delete flow fail", extra={
                    'flow_id': flow.pk,
                    'flow_name': flow.name,
                    'flow_uuid': flow.uuid,
                    'ex': ex,
                    'user': user.email,
                    'org_id': org.id,
                    'org_name': org.name,
                    'org_uuid': org.uuid,
                })
                raise ex
            #endtry
        #endfor
    #enddef apply_action_delete

#endclass FlowOverrides
