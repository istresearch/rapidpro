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
def chat_mode_class(obj):
    scheme: str = obj.schemes[0]
    if scheme.startswith('pm_'):
        return PM_CHANNEL_MODES[PM_Scheme2Mode[scheme]].iconclass
    else:
        return 'glyph icon-phone'
    #endif
#enddef chat_mode_class

@register.filter
def chat_mode_label(obj):
    scheme: str = obj.schemes[0]
    if scheme.startswith('pm_'):
        return PM_CHANNEL_MODES[PM_Scheme2Mode[scheme]].label
    else:
        return 'SMS'
    #endif
#enddef chat_mode_label
