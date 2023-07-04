from engage.api.exceptions import ValueException

def _var_dump( obj ):
    """
    Return a printable representation of an object for debugging\n
    @see https://stackoverflow.com/a/387402\n
    :param obj: The thing to dump.
    :return: Returns the nested thing to dump.
    """
    newobj = obj
    if '__dict__' in dir(obj) and not isinstance(obj, dict):
        newobj = obj.__dict__
        if ' object at ' in str(obj) and 'has_key' in newobj and not newobj.has_key('__type__'):
            newobj['__type__'] = str(obj)
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
    from copy import deepcopy
    try:
        pprint(_var_dump(deepcopy(aThing)))
    except:
        print(f"error, skipping '{aThing}'")
    #endtry

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
