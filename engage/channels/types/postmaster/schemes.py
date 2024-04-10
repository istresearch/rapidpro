from collections import namedtuple

from django.utils.translation import gettext_lazy as _


# notes: iconclass can be a bootstrap icon glyph (icon-*); some will need 'pm-icon' to ensure css works right, or
#        use a class that does _not_ begin with "icon-" and add to engage/static/engage/less/engage.less near
#        "temba-modax#send-via-pm_element" using similar properties; remember to add the icon to engage/static/engage/img.
Schemes_Meta = namedtuple('Postmaster_Schemes_Meta', 'scheme urn_name label iconclass')

PM_CHANNEL_MODES = {
    "ELE":    Schemes_Meta("pm_element",    _("Postmaster Element"),    _("Postmaster Element Identifier"),    "icon-pm_element"),
    "EMAIL":  Schemes_Meta("pm_email",      _("Postmaster Email"),      _("Postmaster Email Identifier"),      "icon-envelop"),
    "FB":     Schemes_Meta("pm_facebook",   _("Postmaster Facebook"),   _("Postmaster Facebook Identifier"),   "icon-facebook"),
    "FBM":    Schemes_Meta("pm_fbm",        _("Postmaster Messenger"),  _("Postmaster Messenger Identifier"),  "icon-tembatoo-fbm pm-icon"),
    "IMO":    Schemes_Meta("pm_imo",        _("Postmaster IMO"),        _("Postmaster IMO Identifier"),        "icon-tembatoo-imo pm-icon"),
    "IG":     Schemes_Meta("pm_instagram",  _("Postmaster Instagram"),  _("Postmaster Instagram Identifier"),  "icon-tembatoo-instagram pm-icon"),
    "KAKAO":  Schemes_Meta("pm_kakao",      _("Postmaster Kakao"),      _("Postmaster Kakao Identifier"),      "icon-tembatoo-kakao pm-icon"),
    "LN":     Schemes_Meta("pm_line",       _("Postmaster Line"),       _("Postmaster Line Identifier"),       "icon-line"),
    "MBX":    Schemes_Meta("pm_mobyx",      _("Postmaster Mobyx"),      _("Postmaster Mobyx Identifier"),      "icon-tembatoo-mobyx pm-icon"),
    "SIG":    Schemes_Meta("pm_signal",     _("Postmaster Signal"),     _("Postmaster Signal Identifier"),     "icon-pm_signal"),
    "TG":     Schemes_Meta("pm_telegram",   _("Postmaster Telegram"),   _("Postmaster Telegram Identifier"),   "icon-telegram"),
    "TWTR":   Schemes_Meta("pm_twitter",    _("Postmaster Twitter"),    _("Postmaster Twitter Identifier"),    "icon-twitter"),
    "VB":     Schemes_Meta("pm_viber",      _("Postmaster Viber"),      _("Postmaster Viber Identifier"),      "icon-viber pm-icon"),
    "VK":     Schemes_Meta("pm_vk",         _("Postmaster VK"),         _("Postmaster VK Identifier"),         "icon-vk pm-icon"),
    "WA":     Schemes_Meta("pm_whatsapp",   _("Postmaster WhatsApp"),   _("Postmaster WhatsApp Identifier"),   "icon-whatsapp"),
    "SESS":   Schemes_Meta("pm_session",    _("Postmaster Session"),    _("Postmaster Session Identifier"),    "icon-pm_session"),
    "REDDIT": Schemes_Meta("pm_reddit",     _("Postmaster Reddit"),     _("Postmaster Reddit Identifier"),     "icon-pm_reddit"),
    "MAST":   Schemes_Meta("pm_mastodon",   _("Postmaster Mastodon"),   _("Postmaster Mastodon Identifier"),   "icon-pm_mastodon"),
    "YT":     Schemes_Meta("pm_youtube",    _("Postmaster Youtube"),    _("Postmaster Youtube Identifier"),    "icon-pm_youtube"),
    "TIK":    Schemes_Meta("pm_tiktok",     _("Postmaster TikTok"),     _("Postmaster TikTok Identifier"),     "icon-pm_tiktok"),
    "PM":     Schemes_Meta("pm_service",    _("Postmaster Device"),     _("Postmaster Service Channel"),       "icon-pm_service"),
}

PM_Scheme2Mode = { val.scheme: key  for key, val in PM_CHANNEL_MODES.items() }
PM_Scheme_Icons = { ico.scheme: ico.iconclass for ico in PM_CHANNEL_MODES.values() }
PM_Scheme_Labels = tuple( (x.scheme, x.label) for x in PM_CHANNEL_MODES.values() )
PM_Scheme_Default_Chats = (
  ("SMS", _("TEL")),
) + tuple( (mode, x.scheme) for mode, x in PM_CHANNEL_MODES.items() )
