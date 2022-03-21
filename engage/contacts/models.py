from collections import namedtuple

from django.utils.translation import ugettext_lazy as _

class PM_Schemes:
    """
    Postmaster schemes
    """
    PM_ELEMENT_SCHEME = "pm_element"
    PM_EMAIL_SCHEME = "pm_email"
    PM_FACEBOOK_SCHEME = "pm_facebook"
    PM_FBM_SCHEME = "pm_fbm"
    PM_IMO_SCHEME = "pm_imo"
    PM_INSTAGRAM_SCHEME = "pm_instagram"
    PM_KAKAO_SCHEME = "pm_kakao"
    PM_LINE_SCHEME = "pm_line"
    PM_MOBYX_SCHEME = "pm_mobyx"
    PM_SIGNAL_SCHEME = "pm_signal"
    PM_TELEGRAM_SCHEME = "pm_telegram"
    PM_TWITTER_SCHEME = "pm_twitter"
    PM_VIBER_SCHEME = "pm_viber"
    PM_VK_SCHEME = "pm_vk"
    PM_WHATSAPP_SCHEME = "pm_whatsapp"

Postmaster_Schemes_Meta = namedtuple('Postmaster_Schemes_Meta', 'scheme label iconclass mode mode_label')
PM_Schemes_Meta = [
    Postmaster_Schemes_Meta(PM_Schemes.PM_ELEMENT_SCHEME, _("Postmaster Element Identifier"), "icon-element pm-icon", "ELE", _("Element")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_EMAIL_SCHEME, _("Postmaster Email Identifier"), "icon-envelop", "EMAIL", _("Email")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_FACEBOOK_SCHEME, _("Postmaster Facebook Identifier"), "icon-facebook", "FB", _("Facebook")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_FBM_SCHEME, _("Postmaster Messenger Identifier"), "icon-tembatoo-fbm pm-icon", "FBM", _("FBM")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_IMO_SCHEME, _("Postmaster IMO Identifier"), "icon-tembatoo-imo pm-icon", "IMO", _("IMO")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_INSTAGRAM_SCHEME, _("Postmaster Instagram Identifier"), "icon-tembatoo-instagram pm-icon", "IG", _("Instagram")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_KAKAO_SCHEME, _("Postmaster Kakao Identifier"), "icon-tembatoo-kakao pm-icon", "KAKAO", _("KAKAO")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_LINE_SCHEME, _("Postmaster Line Identifier"), "icon-line", "LN", _("LINE")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_MOBYX_SCHEME, _("Postmaster Mobyx Identifier"), "icon-tembatoo-mobyx pm-icon", "MBX", _("Mobyx")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_SIGNAL_SCHEME, _("Postmaster Signal Identifier"), "icon-signal pm-icon", "SIG", _("SIGNAL")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_TELEGRAM_SCHEME, _("Postmaster Telegram Identifier"), "icon-telegram", "TG", _("Telegram")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_TWITTER_SCHEME, _("Postmaster Twitter Identifier"), "icon-twitter", "TWTR", _("TWITTER")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_VIBER_SCHEME, _("Postmaster Viber Identifier"), "icon-viber pm-icon", "VB", _("VIBER")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_VK_SCHEME, _("Postmaster VK Identifier"), "icon-vk pm-icon", "VK", _("VK")),
    Postmaster_Schemes_Meta(PM_Schemes.PM_WHATSAPP_SCHEME, _("Postmaster WhatsApp Identifier"), "icon-whatsapp", "WA", _("WhatsApp")),
]

PM_Scheme_Icons = { ico.scheme: ico.iconclass for ico in PM_Schemes_Meta }
PM_Scheme_Labels = tuple( (x.scheme, x.label) for x in PM_Schemes_Meta )
PM_Scheme_Default_Chats = (
  ("SMS", _("TEL")),
) + tuple( (x.mode, x.mode_label) for x in PM_Schemes_Meta )
