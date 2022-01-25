from django.utils.translation import ugettext_lazy as _

from ...models import TicketerType
from .views import ConnectView


class InternalType(TicketerType):
    """
    Type for using RapidPro itself as the ticketer.
    """

    name = "Internal"
    slug = "internal"
    icon = "icon-channel-external"

    connect_view = ConnectView
    connect_blurb = _("Enabling this will allow you to handle tickets within {{brand.name}}.")

    def is_available_to(self, user):
        return not user.get_org().ticketers.filter(ticketer_type=self.slug, is_active=True).exists()
