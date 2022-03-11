import logging
from rest_framework import serializers
from rest_framework.exceptions import ParseError

from .exceptions import FinancialException

class WriteSerializer(serializers.Serializer):
    """
    The normal REST framework way is to have the view decide if it's an update on existing instance or a create for a
    new instance. Since logic for that gets relatively complex, have the serializer make that call.
    """

    def run_validation(self, data=serializers.empty):
        logger = logging.getLogger(__name__)
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

        return super().run_validation(data)
