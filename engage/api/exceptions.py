from rest_framework import status
from rest_framework.exceptions import APIException

from engage.utils.class_overrides import MonkeyPatcher


class ExceptionWithCauseMixin:

    def withCause(cls: type[Exception], cause: str = 'Unknown', msg: str = 'Derp'):
        return cls(detail={"error": {
            'cause': cause,
            'message': msg,
        }})
    #enddef withCause

    def with_cause(cls: type[Exception], cause: str = 'Unknown', msg: str = 'Derp'):
        return cls.withCause(cause, msg)
    #enddef with_cause

#endclass ExceptionWithCauseMixin

class APIExceptionOverride(MonkeyPatcher, ExceptionWithCauseMixin):
    patch_class = APIException
    """
    append a class method to the generic APIException class so we can start
    using a more standardized API response especially when an error occurs.
    """
    pass
#endclass APIExceptionOverride

class BrokenLeg(ExceptionWithCauseMixin, APIException):
    pass

class ValueException(ExceptionWithCauseMixin, ValueError):
    pass

class FinancialException(BrokenLeg):
    status_code = status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS
    default_detail = {'error': {'cause': 'unavailable', 'message': 'Unavailable, for reasons.'}}
    default_code = 'unavailable'
#endclass FinancialException
