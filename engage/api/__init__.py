from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.api.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.api"
    label = "engage_api"
    verbose_name = "Engage API"


# append a static method to the generic APIException class so we can start
#   using a more standardized API response especially when an error occurs.
from rest_framework.exceptions import APIException
def _ExceptionResponseWithCause(cls, cause='Unknown', msg='Derp'):
    return cls(detail={"error": {
        'cause': cause,
        'message': msg,
    }})
setattr(APIException, 'withCause', classmethod(_ExceptionResponseWithCause))
