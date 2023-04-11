# append a static method to the generic APIException class so we can start
#   using a more standardized API response especially when an error occurs.
from rest_framework.exceptions import APIException
def _ExceptionResponseWithCause(cls, cause='Unknown', msg='Derp'):
    return cls(detail={"error": {
        'cause': cause,
        'message': msg,
    }})
setattr(APIException, 'withCause', classmethod(_ExceptionResponseWithCause))
