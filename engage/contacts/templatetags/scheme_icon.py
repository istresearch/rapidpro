from django import template

from temba.contacts.templatetags.contacts import URN_SCHEME_ICONS


register = template.Library()

@register.filter
def scheme_icon(scheme):
    return URN_SCHEME_ICONS.get(scheme, "")
