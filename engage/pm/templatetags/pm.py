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
def chat_mode_class(chat_mode_or_obj):
    if isinstance(chat_mode_or_obj, str):
        chat_mode = chat_mode_or_obj
    else:
        scheme: str = chat_mode_or_obj.schemes[0]
        if scheme.startswith('pm_'):
            chat_mode = PM_Scheme2Mode[scheme]
        else:
            chat_mode = 'SMS'
        #endif
    #endif
    if chat_mode in PM_CHANNEL_MODES:
        return PM_CHANNEL_MODES[chat_mode].iconclass
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

@register.filter
def chat_mode_app(chat_mode_apps, chat_mode):
    return chat_mode_apps.get(chat_mode, {})
#enddef chat_mode_app
