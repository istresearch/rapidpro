from uuid import uuid4

from django.http import HttpResponseRedirect
from django.urls import reverse
from temba.utils import analytics

from temba.orgs.models import BWI_ACCOUNT_SID, BWI_ACCOUNT_TOKEN, BWI_APPLICATION_SID
from temba.channels.types.bandwidth.views import ClaimView as BWClaimView
from ...models import Channel


class ClaimView(BWClaimView):
    uuid = None

    def __init__(self, channel_type):
        super().__init__(channel_type)
        self.account = None
        self.client = None

    def get_claim_url(self):
        return reverse("channels.types.bandwidth_international.claim")
    
    def get_success_url(self):
            return reverse("channels.channel_read", args=[self.uuid])

    form_class = BWClaimView.Form
    submit_button_name = "Save"
    success_url = "@channels.types.bandwidth_international.claim"
    field_config = dict(bw_account_sid=dict(label=""), bw_account_token=dict(label=""))
    success_message = "Bandwidth Account successfully connected."

    def form_valid(self, form):
        bwi_account_sid = form.cleaned_data["bwi_account_sid"]
        bwi_account_token = form.cleaned_data["bwi_account_token"]
        bwi_account_secret = form.cleaned_data["bwi_account_secret"]
        bwi_phone_number = form.cleaned_data["bwi_phone_number"]
        bwi_application_sid = form.cleaned_data["bwi_application_sid"]
        bwi_country_sid = form.cleaned_data["bwi_country"]

        org = self.org
        org.connect_bandwidth(bwi_account_sid, bwi_account_token, bwi_account_secret, bwi_phone_number,
                              bwi_application_sid, self.request.user)
        org.save()

        channel = self.claim_number(self.request.user, bwi_phone_number, bwi_country_sid, Channel.ROLE_SEND + Channel.ROLE_CALL)

        self.uuid = channel.uuid
        return HttpResponseRedirect(self.get_success_url())

    def claim_number(self, user, phone_number, country, role):
        org = user.get_org()
        self.uuid = uuid4()
        callback_domain = org.get_brand_domain()
        org_config = org.config
        config = {
            Channel.CONFIG_APPLICATION_SID: org_config[BWI_APPLICATION_SID],
            Channel.CONFIG_ACCOUNT_SID: org_config[BWI_ACCOUNT_SID],
            Channel.CONFIG_AUTH_TOKEN: org_config[BWI_ACCOUNT_TOKEN],
            Channel.CONFIG_CALLBACK_DOMAIN: callback_domain,
        }

        channel = Channel.create(
            org, user, country, "BWI", name=org_config[BWI_ACCOUNT_SID], address=phone_number, role=role, config=config, uuid=self.uuid
        )

        analytics.track(user.username, "temba.channel_claim_bandwidth_international", properties=dict(number=phone_number))

        return channel