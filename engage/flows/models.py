import logging

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import MonkeyPatcher

from packaging.version import Version

from temba import mailroom
from temba.flows.models import Flow, FlowVersionConflictException, FlowUserConflictException, get_flow_user
from temba.utils import analytics


class FlowOverrides(MonkeyPatcher):
    patch_class = Flow

    TYPE_CHOICES = (
        (Flow.TYPE_MESSAGE, _("Messaging")),
        (Flow.TYPE_VOICE, _("Phone Call")),
        (Flow.TYPE_BACKGROUND, _("Background")),
        # (Flow.TYPE_SURVEY, _("Surveyor")), # P4-1483
    )

    def create(
        cls: type(Flow),
        org,
        user,
        name,
        flow_type=Flow.TYPE_MESSAGE,
        expires_after_minutes=0,
        base_language="base",
        create_revision=False,
        channels=None,
        **kwargs,
    ):
        assert cls.is_valid_name(name), f"'{name}' is not a valid flow name"
        assert not expires_after_minutes or cls.is_valid_expires(flow_type, expires_after_minutes)

        flow = cls.objects.create(
            org=org,
            name=name,
            flow_type=flow_type,
            expires_after_minutes=expires_after_minutes or cls.EXPIRES_DEFAULTS[flow_type],
            base_language=base_language,
            saved_by=user,
            created_by=user,
            modified_by=user,
            version_number=Flow.CURRENT_SPEC_VERSION,
            metadata={'channels': channels} if channels else None,
            **kwargs,
        )

        if create_revision:
            flow.save_revision(
                user,
                {
                    Flow.DEFINITION_NAME: flow.name,
                    Flow.DEFINITION_UUID: flow.uuid,
                    Flow.DEFINITION_SPEC_VERSION: Flow.CURRENT_SPEC_VERSION,
                    Flow.DEFINITION_LANGUAGE: base_language,
                    Flow.DEFINITION_TYPE: Flow.GOFLOW_TYPES[flow_type],
                    Flow.DEFINITION_NODES: [],
                    Flow.DEFINITION_UI: {},
                    'channels': channels if channels else [],
                },
            )

        analytics.track(user, "temba.flow_created", dict(name=name, uuid=flow.uuid))
        return flow
    #enddef create

    def save_revision(self: Flow, user, definition) -> tuple:
        """
        Saves a new revision for this flow, validation will be done on the definition first
        """
        if Version(definition.get(Flow.DEFINITION_SPEC_VERSION)) < Version(Flow.INITIAL_GOFLOW_VERSION):
            raise FlowVersionConflictException(definition.get(Flow.DEFINITION_SPEC_VERSION))

        current_revision = self.get_current_revision()

        if current_revision:
            # check we aren't walking over someone else
            definition_revision = definition.get(Flow.DEFINITION_REVISION)
            if definition_revision is not None and definition_revision < current_revision.revision:
                raise FlowUserConflictException(self.saved_by, self.saved_on)

            revision = current_revision.revision + 1
        else:
            revision = 1

        if self.metadata is None:
            self.metadata = {}

        # update metadata from database object
        definition[Flow.DEFINITION_UUID] = self.uuid
        definition[Flow.DEFINITION_NAME] = self.name
        definition[Flow.DEFINITION_REVISION] = revision
        definition[Flow.DEFINITION_EXPIRE_AFTER_MINUTES] = self.expires_after_minutes
        definition['channels'] = self.metadata.get('channels', [])

        # inspect the flow (with optional validation)
        flow_info = mailroom.get_client().flow_inspect(self.org.id, definition)
        dependencies = flow_info[Flow.INSPECT_DEPENDENCIES]
        issues = flow_info[Flow.INSPECT_ISSUES]

        if user is None:
            is_system_rev = True
            user = get_flow_user(self.org)
        else:
            is_system_rev = False

        with transaction.atomic():
            new_metadata = self.metadata | Flow.get_metadata(flow_info)

            # update our flow fields
            self.base_language = definition.get(Flow.DEFINITION_LANGUAGE, None)
            self.version_number = Flow.CURRENT_SPEC_VERSION
            self.has_issues = len(issues) > 0
            self.metadata = new_metadata
            self.modified_by = user
            self.modified_on = timezone.now()
            fields = ["base_language", "version_number", "has_issues", "metadata", "modified_by", "modified_on"]

            if not is_system_rev:
                self.saved_by = user
                self.saved_on = timezone.now()
                fields += ["saved_by", "saved_on"]

            self.save(update_fields=fields)

            # create our new revision
            revision = self.revisions.create(
                definition=definition,
                created_by=user,
                modified_by=user,
                spec_version=Flow.CURRENT_SPEC_VERSION,
                revision=revision,
            )

            self.update_dependencies(dependencies)

        return revision, issues
    #enddef save_revision

    def apply_action_delete(cls: type[Flow], user, flows):
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
