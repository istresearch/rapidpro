from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.api"
    label = "engage_api"
    verbose_name = "Engage API"

    def ready(self):
        from .serializers import MsgBulkActionSerializerOverride
        MsgBulkActionSerializerOverride.applyPatches()

        from .serializers import FlowStartWriteSerializerOverride
        FlowStartWriteSerializerOverride.applyPatches()

        from .serializers import ContactReadSerializerOverrides
        ContactReadSerializerOverrides.applyPatches()

        from .exceptions import APIExceptionOverride
        APIExceptionOverride.applyPatches()

        from .support import APITokenAuthenticationOverride
        APITokenAuthenticationOverride.applyPatches()

        from .endpoint.broadcasts import BroadcastsEndpointOverrides
        BroadcastsEndpointOverrides.applyPatches()

        from .endpoint.contacts import ContactsEndpointOverrides
        ContactsEndpointOverrides.applyPatches()

        from .endpoint.messages import MessagesEndpointOverrides
        MessagesEndpointOverrides.applyPatches()
    #enddef ready

#endclass AppConfig
