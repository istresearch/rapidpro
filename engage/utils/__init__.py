from django.apps import AppConfig as BaseAppConfig

default_app_config = 'engage.utils.AppConfig'

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.utils"
    label = "engage_utils"
    verbose_name = "Engage Utilities"


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
    raise ValueError(f"[{arg_name}] not defined.")
