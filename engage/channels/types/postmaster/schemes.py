from collections import namedtuple

from django.utils.translation import gettext_lazy as _

class PM_Schemes:
    """
    Postmaster schemes, they must all be unique and start with 'pm_'.
    """
    PM_ELEMENT_SCHEME       = "pm_element"
    PM_EMAIL_SCHEME         = "pm_email"
    PM_FACEBOOK_SCHEME      = "pm_facebook"
    PM_FBM_SCHEME           = "pm_fbm"
    PM_IMO_SCHEME           = "pm_imo"
    PM_INSTAGRAM_SCHEME     = "pm_instagram"
    PM_KAKAO_SCHEME         = "pm_kakao"
    PM_LINE_SCHEME          = "pm_line"
    PM_MOBYX_SCHEME         = "pm_mobyx"
    PM_SIGNAL_SCHEME        = "pm_signal"
    PM_TELEGRAM_SCHEME      = "pm_telegram"
    PM_TWITTER_SCHEME       = "pm_twitter"
    PM_VIBER_SCHEME         = "pm_viber"
    PM_VK_SCHEME            = "pm_vk"
    PM_WHATSAPP_SCHEME      = "pm_whatsapp"
    PM_SESSION_SCHEME       = "pm_session"
    PM_REDDIT_SCHEME        = "pm_reddit"
    PM_MASTODON_SCHEME      = "pm_mastodon"
    PM_YOUTUBE_SCHEME       = "pm_youtube"

# notes: iconclass can be a bootstrap icon glyph (icon-*); some will need 'pm-icon' to ensure css works right, or
#        use a class that does _not_ begin with "icon-" and add to engage/static/engage/less/engage.less near
#        "temba-modax#send-via-pm_element" using similar properties; remember to add the icon to engage/static/engage/img.
Schemes_Meta = namedtuple('Postmaster_Schemes_Meta', 'scheme label iconclass mode mode_label')
PM_Schemes_Meta = [
    Schemes_Meta(PM_Schemes.PM_ELEMENT_SCHEME,    _("Postmaster Element Identifier"),   "element-chat",                    "ELE",   _("Element")),
    Schemes_Meta(PM_Schemes.PM_EMAIL_SCHEME,      _("Postmaster Email Identifier"),     "icon-envelop",                    "EMAIL", _("Email")),
    Schemes_Meta(PM_Schemes.PM_FACEBOOK_SCHEME,   _("Postmaster Facebook Identifier"),  "icon-facebook",                   "FB",    _("Facebook")),
    Schemes_Meta(PM_Schemes.PM_FBM_SCHEME,        _("Postmaster Messenger Identifier"), "icon-tembatoo-fbm pm-icon",       "FBM",   _("FBM")),
    Schemes_Meta(PM_Schemes.PM_IMO_SCHEME,        _("Postmaster IMO Identifier"),       "icon-tembatoo-imo pm-icon",       "IMO",   _("IMO")),
    Schemes_Meta(PM_Schemes.PM_INSTAGRAM_SCHEME,  _("Postmaster Instagram Identifier"), "icon-tembatoo-instagram pm-icon", "IG",    _("Instagram")),
    Schemes_Meta(PM_Schemes.PM_KAKAO_SCHEME,      _("Postmaster Kakao Identifier"),     "icon-tembatoo-kakao pm-icon",     "KAKAO", _("KAKAO")),
    Schemes_Meta(PM_Schemes.PM_LINE_SCHEME,       _("Postmaster Line Identifier"),      "icon-line",                       "LN",    _("LINE")),
    Schemes_Meta(PM_Schemes.PM_MOBYX_SCHEME,      _("Postmaster Mobyx Identifier"),     "icon-tembatoo-mobyx pm-icon",     "MBX",   _("Mobyx")),
    Schemes_Meta(PM_Schemes.PM_SIGNAL_SCHEME,     _("Postmaster Signal Identifier"),    "signal-chat",                     "SIG",   _("SIGNAL")),
    Schemes_Meta(PM_Schemes.PM_TELEGRAM_SCHEME,   _("Postmaster Telegram Identifier"),  "icon-telegram",                   "TG",    _("Telegram")),
    Schemes_Meta(PM_Schemes.PM_TWITTER_SCHEME,    _("Postmaster Twitter Identifier"),   "icon-twitter",                    "TWTR",  _("TWITTER")),
    Schemes_Meta(PM_Schemes.PM_VIBER_SCHEME,      _("Postmaster Viber Identifier"),     "icon-viber pm-icon",              "VB",    _("VIBER")),
    Schemes_Meta(PM_Schemes.PM_VK_SCHEME,         _("Postmaster VK Identifier"),        "icon-vk pm-icon",                 "VK",    _("VK")),
    Schemes_Meta(PM_Schemes.PM_WHATSAPP_SCHEME,   _("Postmaster WhatsApp Identifier"),  "icon-whatsapp",                   "WA",    _("WhatsApp")),
    Schemes_Meta(PM_Schemes.PM_SESSION_SCHEME,    _("Postmaster Session Identifier"),   "icon-session-messenger",          "SESS",  _("Session")),
    Schemes_Meta(PM_Schemes.PM_REDDIT_SCHEME,     _("Postmaster Reddit Identifier"),    "icon-reddit",                     "REDDIT",_("Reddit")),
    Schemes_Meta(PM_Schemes.PM_MASTODON_SCHEME,   _("Postmaster Mastodon Identifier"),  "icon-mastodon",                   "MAST",  _("Mastodon")),
    Schemes_Meta(PM_Schemes.PM_YOUTUBE_SCHEME,    _("Postmaster Youtube Identifier"),   "icon-youtube",                    "YT",    _("Youtube")),
]

PM_Scheme_Icons = { ico.scheme: ico.iconclass for ico in PM_Schemes_Meta }
PM_Scheme_Labels = tuple( (x.scheme, x.label) for x in PM_Schemes_Meta )
PM_Scheme_Default_Chats = (
  ("SMS", _("TEL")),
) + tuple( (x.mode, x.mode_label) for x in PM_Schemes_Meta )
