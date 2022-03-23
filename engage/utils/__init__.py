from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.utils.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.utils"
    label = "engage_utils"
    verbose_name = "Engage Utilities"

import re
from engage.api.exceptions import ValueException

def _var_dump( obj ):
    """
    Return a printable representation of an object for debugging\n
    @see https://stackoverflow.com/a/387402\n
    :param obj: The thing to dump.
    :return: Returns the nested thing to dump.
    """
    newobj=obj
    if '__dict__' in dir(obj):
        newobj=obj.__dict__
        if ' object at ' in str(obj) and not newobj.has_key('__type__'):
            newobj['__type__']=str(obj)
        for attr in newobj:
            newobj[attr] = _var_dump(newobj[attr])
    return newobj

def var_dump( aThing, aMsg=None ):
    """
    Debug dump a var to STDOUT.
    :param aThing: var to print out.
    :param aMsg: an optional message to print out along with the var.
    """
    if aMsg:
        print(aMsg)
    from pprint import pprint
    pprint(_var_dump(aThing))

def get_required_arg(arg_name, kwargs, bCheckForEmpty=True):
    """
    Check for arg_name in kwargs and return its value, if found.
    If bCheckForEmpty is True and value is not found or is empty
    string, then a ValueError will be raised.
    :param arg_name: string key to check kwargs.
    :param kwargs: the array of args to check.
    :param bCheckForEmpty: optionally raise a ValueError if value is empty/None.
    :return: Returns the value of the arg_name found.
    """
    if arg_name in kwargs and kwargs[arg_name] is not None:
        if not bCheckForEmpty or len(kwargs[arg_name]) > 0:
            return kwargs[arg_name]
    raise ValueException.withCause(cause='missing argument', msg=f"[{arg_name}] not defined.")

def _mg_for_cap_words( aMatchGroup: re.Match[str] ) -> str:
    """
    process regular expression match groups for word upper-casing problem\n
    @see https://stackoverflow.com/a/1549983\n
    :param aMatchGroup: re match group
    :return: Return a string with the first letter in word capitalized.
    """
    return aMatchGroup.group(1) + aMatchGroup.group(2).upper()

def cap_words( aString: str ):
    """
    Capitalize words in a string, but leave all other chars alone.\n
    e.g. input: "they're bill's friends from the UK"\n
    output: "They're Bill's Friends From The UK"\n
    @see https://stackoverflow.com/a/1549983\n
    :param aString: the string to work on
    :return: Returns the string with words capitalized.
    """
    return re.sub("(^|\s)(\S)", _mg_for_cap_words, aString)
