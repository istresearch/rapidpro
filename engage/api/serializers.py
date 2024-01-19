import logging
from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ParseError

from temba.api.v2.serializers import (
    MsgBulkActionSerializer,
    FlowStartWriteSerializer, normalize_extra,
)

from engage.utils.class_overrides import MonkeyPatcher

from .exceptions import FinancialException

class WriteSerializer(serializers.Serializer):
    """
    The normal REST framework way is to have the view decide if it's an update on existing instance or a create for a
    new instance. Since logic for that gets relatively complex, have the serializer make that call.
    """

    def run_validation(self, data=serializers.empty):
        logger = logging.getLogger()
        if not isinstance(data, dict):
            raise ParseError.withCause(
                cause='JSON Parse Failure',
                msg='Request body should be a single JSON object',
            )

        theOrg = self.context["org"]
        if theOrg.is_flagged or theOrg.is_suspended:
            state = "flagged" if theOrg.is_flagged else "suspended"
            logger.error(f"API called using a token from a {state} workspace", extra={
                'org': theOrg,
                'org_id': theOrg.id,
                'org_uuid': theOrg.uuid,
                'flagged': theOrg.is_flagged,
                'suspended': theOrg.is_suspended,
                'api_call': self.context['request'],
            })
            raise FinancialException.withCause(
                cause=f"workspace {state}",
                msg=f"Sorry, your workspace is currently {state}. Please contact support.",
            )
        # since we will be overriding a diff class with this method, be explicit with super().
        return super(serializers.Serializer, self).run_validation(data)
    #enddef run_validation

#endclass WriteSerializer


class MsgBulkActionSerializerOverride(MonkeyPatcher):
    patch_class = MsgBulkActionSerializer

    def validate_messages(self: MsgBulkActionSerializer, value):
        if 'request' in self.context and 'action' in self.context['request'].data:
            return value
        else:
            return self.super_validate_messages(value)
        #endif
    #enddef validate_messages

#endclass MsgBulkActionSerializerOverride


class FlowStartWriteSerializerOverride(MonkeyPatcher):
    patch_class = FlowStartWriteSerializer

    def validate_extra(self, value):
        # request is parsed by DRF.JSONParser, and if extra is a valid json it gets deserialized as dict
        # in any other case we need to raise a ValidationError
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be a valid JSON object")

        max_text_leng = settings.MSG_FIELD_SIZE
        if isinstance(value, str):
            return value[:max_text_leng]
        else:
            return normalize_extra(value)
    #enddef validate_extra

#endclass FlowStartWriteSerializerOverride
