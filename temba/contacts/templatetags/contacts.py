from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from temba.contacts.models import ContactURN, EMAIL_SCHEME, EXTERNAL_SCHEME, FACEBOOK_SCHEME, FCM_SCHEME
from temba.contacts.models import TELEGRAM_SCHEME, TEL_SCHEME, TWITTER_SCHEME, TWILIO_SCHEME, LINE_SCHEME
from temba.ivr.models import IVRCall
from temba.msgs.models import ERRORED, FAILED

register = template.Library()

URN_SCHEME_ICONS = {
    TEL_SCHEME: 'icon-mobile-2',
    TWITTER_SCHEME: 'icon-twitter',
    TWILIO_SCHEME: 'icon-twilio_original',
    EMAIL_SCHEME: 'icon-envelop',
    FACEBOOK_SCHEME: 'icon-facebook',
    TELEGRAM_SCHEME: 'icon-telegram',
    LINE_SCHEME: 'icon-line',
    EXTERNAL_SCHEME: 'icon-channel-external',
    FCM_SCHEME: 'icon-fcm'
}

ACTIVITY_ICONS = {
    'EventFire': 'icon-clock',
    'FlowRun': 'icon-tree-2',
    'Broadcast': 'icon-bullhorn',
    'Incoming': 'icon-bubble-user',
    'Outgoing': 'icon-bubble-right',
    'Failed': 'icon-bubble-notification',
    'Delivered': 'icon-bubble-check',
    'Call': 'icon-phone',
    'IVRCall': 'icon-call-outgoing',
    'DTMF': 'icon-call-incoming',
    'Expired': 'icon-clock',
    'Interrupted': 'icon-warning',
    'Completed': 'icon-checkmark',
    'WebHookResult': 'icon-cloud-upload',
}

PLAYABLE_AUDIO_TYPES = {'audio/wav', 'audio/x-wav', 'audio/vnd.wav', 'audio/ogg', 'audio/mp3', 'audio/m4a'}

MISSING_VALUE = '--'


@register.filter
def contact_field(contact, arg):
    value = contact.get_field_display(arg)
    return value or MISSING_VALUE


@register.filter
def short_name(contact, org):
    return contact.get_display(org, short=True)


@register.filter
def name_or_urn(contact, org):
    return contact.get_display(org)


@register.filter
def name(contact, org):
    if contact.name:
        return contact.name
    elif org.is_anon:
        return contact.anon_identifier
    else:
        return MISSING_VALUE


@register.filter
def format_urn(urn, org):
    urn_val = urn.get_display(org=org, international=True)
    if urn_val == ContactURN.ANON_MASK:
        return ContactURN.ANON_MASK_HTML
    return urn_val


@register.filter
def urn(contact, org):
    contact_urn = contact.get_urn()
    if contact_urn:
        return format_urn(contact_urn, org)
    else:
        return MISSING_VALUE


@register.filter
def format_contact(contact, org):
    return contact.get_display(org=org)


@register.filter
def urn_icon(urn):
    return URN_SCHEME_ICONS.get(urn.scheme, '')


@register.filter
def osm_link(geo_url):
    (content_type, delim, loc) = geo_url.partition(':')
    coords = loc.split(',')
    if len(coords) == 2:
        (lat, lng) = coords
        return 'http://www.openstreetmap.org/?mlat=%(lat)s&mlon=%(lng)s#map=18/%(lat)s/%(lng)s' % {"lat": lat, "lng": lng}


@register.filter
def location(geo_url):
    (content_type, delim, loc) = geo_url.partition(':')
    if len(loc.split(',')) == 2:
        return loc


@register.filter
def media_url(media):
    return media.partition(':')[2]


@register.filter
def media_content_type(media):
    content_type, delim, url = media.partition(':')

    if content_type == 'application/octet-stream' and (url.endswith('.ogg') or media.endswith('.oga')):
        content_type = 'audio/ogg'

    return content_type


@register.filter
def media_type(media):
    content_type = media_content_type(media)
    if content_type and '/' in content_type:  # pragma: needs cover
        content_type = content_type.split('/')[0]
    return content_type


@register.filter
def is_playable_audio(content_type):
    return content_type in PLAYABLE_AUDIO_TYPES


@register.filter
def extension(url):  # pragma: needs cover
    return url.rpartition('.')[2]


@register.filter
def activity_icon(item):
    obj = item['obj']

    if item['type'] == 'broadcast':
        icon = 'Failed' if obj.purged_status in ('E', 'F') else 'Broadcast'
    elif item['type'] == 'msg':
        if obj.broadcast and obj.broadcast.recipient_count > 1:
            icon = 'Failed' if obj.status in ('E', 'F') else 'Broadcast'
        elif obj.msg_type == 'V':
            icon = 'DTMF' if obj.direction == 'I' else 'IVRCall'
        elif obj.direction == 'I':
            icon = 'Incoming'
        else:
            if obj.status in ('F', 'E'):
                icon = 'Failed'
            elif obj.status == 'D':
                icon = 'Delivered'
            else:
                icon = 'Outgoing'
    elif item['type'] == 'run-start':
        icon = 'FlowRun'
    elif item['type'] == 'run-exit':
        if obj.exit_type == 'C':
            icon = 'Completed'
        elif obj.exit_type == 'I':
            icon = 'Interrupted'
        else:
            icon = 'Expired'
    else:
        icon = type(obj).__name__

    return mark_safe('<span class="glyph %s"></span>' % (ACTIVITY_ICONS.get(icon, '')))


@register.filter
def history_class(item):
    obj = item['obj']
    classes = []

    if item['type'] == 'msg':
        classes.append('msg')
        if obj.attachments and obj.attachments[0][:6] == 'video:':
            classes.append('video')
        if obj.status in (ERRORED, FAILED):
            classes.append('warning')
    else:
        classes.append('non-msg')

        if item['type'] == 'webhook-result' and not obj.is_success:
            classes.append('warning')

        if item['type'] == 'call' and obj.status == IVRCall.FAILED:
            classes.append('warning')
    return ' '.join(classes)


@register.filter
def event_time(event):

    unit = event.unit
    if abs(event.offset) == 1:
        if event.unit == 'D':
            unit = _('day')
        elif event.unit == 'M':
            unit = _('minute')
        elif event.unit == 'H':
            unit = _('hour')
    else:
        if event.unit == 'D':
            unit = _('days')
        elif event.unit == 'M':
            unit = _('minutes')
        elif event.unit == 'H':
            unit = _('hours')

    direction = 'after'
    if event.offset < 0:
        direction = 'before'

    return "%d %s %s %s" % (abs(event.offset), unit, direction, event.relative_to.label)
