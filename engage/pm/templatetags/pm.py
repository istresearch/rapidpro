from django import template


register = template.Library()

@register.filter
def sort_by(sort_field):
    if sort_field == "device_name":
        return "name"
    elif sort_field == "device_id":
        return "address"
    return sort_field
#enddef sort_by
