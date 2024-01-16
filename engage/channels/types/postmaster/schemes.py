from collections import namedtuple

from django.utils.translation import gettext_lazy as _


# notes: iconclass can be a bootstrap icon glyph (icon-*); some will need 'pm-icon' to ensure css works right, or
#        use a class that does _not_ begin with "icon-" and add to engage/static/engage/less/engage.less near
#        "temba-modax#send-via-pm_element" using similar properties; remember to add the icon to engage/static/engage/img.
Schemes_Meta = namedtuple('Postmaster_Schemes_Meta', 'scheme label iconclass')

PM_CHANNEL_MODES = {
    "ELE":      Schemes_Meta("pm_element",      _("Postmaster Element Identifier"),     "element-chat"),
    "EMAIL":    Schemes_Meta("pm_email",        _("Postmaster Email Identifier"),       "icon-envelop"),
    "FB":       Schemes_Meta("pm_facebook",     _("Postmaster Facebook Identifier"),    "icon-facebook"),
    "FBM":      Schemes_Meta("pm_fbm",          _("Postmaster Messenger Identifier"),   "icon-tembatoo-fbm pm-icon"),
    "IMO":      Schemes_Meta("pm_imo",          _("Postmaster IMO Identifier"),         "icon-tembatoo-imo pm-icon"),
    "IG":       Schemes_Meta("pm_instagram",    _("Postmaster Instagram Identifier"),   "icon-tembatoo-instagram pm-icon"),
    "KAKAO":    Schemes_Meta("pm_kakao",        _("Postmaster Kakao Identifier"),       "icon-tembatoo-kakao pm-icon"),
    "LN":       Schemes_Meta("pm_line",         _("Postmaster Line Identifier"),        "icon-line"),
    "MBX":      Schemes_Meta("pm_mobyx",        _("Postmaster Mobyx Identifier"),       "icon-tembatoo-mobyx pm-icon"),
    "SIG":      Schemes_Meta("pm_signal",       _("Postmaster Signal Identifier"),      "signal-chat"),
    "TG":       Schemes_Meta("pm_telegram",     _("Postmaster Telegram Identifier"),    "icon-telegram"),
    "TWTR":     Schemes_Meta("pm_twitter",      _("Postmaster Twitter Identifier"),     "icon-twitter"),
    "VB":       Schemes_Meta("pm_viber",        _("Postmaster Viber Identifier"),       "icon-viber pm-icon"),
    "VK":       Schemes_Meta("pm_vk",           _("Postmaster VK Identifier"),          "icon-vk pm-icon"),
    "WA":       Schemes_Meta("pm_whatsapp",     _("Postmaster WhatsApp Identifier"),    "icon-whatsapp"),
    "SESS":     Schemes_Meta("pm_session",      _("Postmaster Session Identifier"),     "icon-session-messenger"),
    "REDDIT":   Schemes_Meta("pm_reddit",       _("Postmaster Reddit Identifier"),      "icon-reddit"),
    "MAST":     Schemes_Meta("pm_mastodon",     _("Postmaster Mastodon Identifier"),    "icon-mastodon"),
    "YT":       Schemes_Meta("pm_youtube",      _("Postmaster Youtube Identifier"),     "icon-youtube"),
    "TIK":      Schemes_Meta("pm_tiktok",       _("Postmaster TikTok Identifier"),      "icon-tiktok"),
    "PM":       Schemes_Meta("pm_service",      _("Postmaster Service Channel"),        "icon-postmaster"),
}

PM_Scheme_Icons = { ico.scheme: ico.iconclass for ico in PM_CHANNEL_MODES.values() }
PM_Scheme_Labels = tuple( (x.scheme, x.label) for x in PM_CHANNEL_MODES.values() )
PM_Scheme_Default_Chats = (
  ("SMS", _("TEL")),
) + tuple( (mode, x.scheme) for mode, x in PM_CHANNEL_MODES.items() )
