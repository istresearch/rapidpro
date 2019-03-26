import requests

from django.conf.urls import url
from django.forms import ValidationError
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from temba.channels.models import Channel
from temba.channels.types.whatsapp.views import ClaimView, RefreshView
from temba.contacts.models import WHATSAPP_SCHEME
from temba.templates.models import ChannelTemplate

from ...models import ChannelType

# Mapping from WhatsApp status to RapidPro status
STATUS_MAPPING = dict(PENDING=ChannelTemplate.STATUS_PENDING, APPROVED=ChannelTemplate.STATUS_APPROVED)

# This maps from WA iso-639-2 codes to our internal 639-3 codes
LANGUAGE_MAPPING = dict(
    af="afr",  # Afrikaans
    sq="sqi",  # Albanian
    ar="ara",  # Arabic
    az="aze",  # Azerbaijani
    bn="ben",  # Bengali
    bg="bul",  # Bulgarian
    ca="cat",  # Catalan
    zh_CN="zho",  # Chinese (CHN)
    zh_HK="yue",  # Chinese (HKG)
    zh_TW="cmn",  # Chinese (TAI)
    hr="hrv",  # Croatian
    cs="ces",  # Czech
    da="dah",  # Danish
    nl="nld",  # Dutch
    en="eng",  # English
    en_GB="eng",  # English (UK)
    en_US="eng",  # English (US)
    et="est",  # Estonian
    fil="fil",  # Filipino
    fi="fin",  # Finnish
    fr="fra",  # French
    de="deu",  # German
    el="ell",  # Greek
    gu="gul",  # Gujarati
    he="enb",  # Hebrew
    hi="hin",  # Hindi
    hu="hun",  # Hungarian
    id="ind",  # Indonesian
    ga="gle",  # Irish
    it="ita",  # Italian
    ja="jpn",  # Japanese
    kn="kan",  # Kannada
    kk="kaz",  # Kazakh
    ko="kor",  # Korean
    lo="lao",  # Lao
    lv="lav",  # Latvian
    lt="lit",  # Lithuanian
    mk="mkd",  # Macedonian
    ms="msa",  # Malay
    mr="mar",  # Marathi
    nb="nob",  # Norwegian
    fa="fas",  # Persian
    pl="pol",  # Polish
    pt_BR="por",  # Portuguese (BR)
    pt_PT="por",  # Portuguese (POR)
    pa="pan",  # Punjabi
    ro="ron",  # Romanian
    ru="rus",  # Russian
    sr="srp",  # Serbian
    sk="slk",  # Slovak
    sl="slv",  # Slovenian
    es="spa",  # Spanish
    es_AR="spa",  # Spanish (ARG)
    es_ES="spa",  # Spanish (SPA)
    es_MX="spa",  # Spanish (MEX)
    sw="swa",  # Swahili
    sv="swe",  # Swedish
    ta="tam",  # Tamil
    te="tel",  # Telugu
    th="tha",  # Thai
    tr="tur",  # Turkish
    uk="ukr",  # Ukrainian
    ur="urd",  # Urdu
    uz="uzb",  # Uzbek
    vi="vie",  # Vietnamese
)

CONFIG_FB_USER_ID = "fb_business_id"
CONFIG_FB_ACCESS_TOKEN = "fb_access_token"


class WhatsAppType(ChannelType):
    """
    A WhatsApp Channel Type
    """

    code = "WA"
    category = ChannelType.Category.SOCIAL_MEDIA

    courier_url = r"^wa/(?P<uuid>[a-z0-9\-]+)/(?P<action>receive)$"

    name = "WhatsApp"
    icon = "icon-whatsapp"

    claim_blurb = _(
        """If you have an enterprise WhatsApp account, you can connect it to communicate with your contacts"""
    )
    claim_view = ClaimView

    schemes = [WHATSAPP_SCHEME]
    max_length = 4096
    attachment_support = True

    def is_available_to(self, user):
        return user.groups.filter(name="Beta")

    def send(self, channel, msg, text):  # pragma: no cover
        raise Exception("Sending WhatsApp messages is only possible via Courier")

    def get_urls(self):
        return [self.get_claim_url(), url(r"^refresh/(?P<uuid>[a-z0-9\-]+)/?$", RefreshView.as_view(), name="refresh")]

    def deactivate(self, channel):
        # deactivate all templates associated with us
        ChannelTemplate.trim(channel, [])

    def activate(self, channel):
        domain = channel.org.get_brand_domain()
        headers = {"Authorization": "Bearer %s" % channel.config[Channel.CONFIG_AUTH_TOKEN]}

        # first set our callbacks
        payload = {"webhooks": {"url": "https://" + domain + reverse("courier.wa", args=[channel.uuid, "receive"])}}
        resp = requests.patch(
            channel.config[Channel.CONFIG_BASE_URL] + "/v1/settings/application", json=payload, headers=headers
        )

        if resp.status_code != 200:
            raise ValidationError(_("Unable to register callbacks: %s", resp.content))

        # update our quotas so we can send at 15/s
        payload = {
            "messaging_api_rate_limit": ["15", "54600", "1000000"],
            "contacts_scrape_rate_limit": "1000000",
            "contacts_api_rate_limit": ["15", "54600", "1000000"],
        }
        resp = requests.patch(
            channel.config[Channel.CONFIG_BASE_URL] + "/v1/settings/application", json=payload, headers=headers
        )

        if resp.status_code != 200:
            raise ValidationError(_("Unable to configure channel: %s", resp.content))
