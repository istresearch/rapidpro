from rest_framework import status
from rest_framework.exceptions import APIException

from engage.api import _ExceptionResponseWithCause


class BrokenLeg(APIException):
    withCause=classmethod(_ExceptionResponseWithCause)

class ValueException(ValueError):
    withCause=classmethod(_ExceptionResponseWithCause)

class FinancialException(BrokenLeg):
    status_code = status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS
    default_detail = {'error': {'cause': 'unavailable', 'message': 'Unavailable, for reasons.'}}
    default_code = 'unavailable'
