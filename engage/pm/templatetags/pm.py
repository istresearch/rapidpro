from django import template

from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES, PM_Scheme2Mode

register = template.Library()

@register.filter
def sort_by(sort_field):
    if sort_field == "device_name":
        return "name"
    elif sort_field == "device_id":
        return "address"
    return sort_field
#enddef sort_by

@register.filter
def pm_scheme_class(pm_scheme_or_obj):
    scheme: str
    if isinstance(pm_scheme_or_obj, str):
        scheme = pm_scheme_or_obj
    else:
        scheme = pm_scheme_or_obj.pm_scheme
    #endif
    if scheme in PM_Scheme2Mode:
        return PM_CHANNEL_MODES[PM_Scheme2Mode[scheme]].iconclass
    else:
        return 'glyph icon-phone'
    #endif
#enddef pm_scheme_class

@register.filter
def pm_scheme_label(obj):
    scheme: str = obj.pm_scheme
    if scheme in PM_Scheme2Mode:
        return PM_CHANNEL_MODES[PM_Scheme2Mode[scheme]].label
    else:
        return 'SMS'
    #endif
#enddef pm_scheme_label

@register.filter
def pm_scheme_app(pm_scheme_apps, pm_scheme):
    if pm_scheme_apps == "":
        return {}
    #endif
    return pm_scheme_apps.get(pm_scheme, {})
#enddef pm_scheme_app
