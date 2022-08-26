import bandwidth

from engage.utils.class_overrides import ignoreDjangoModelAttrs

from temba.orgs.models import Org


BW_APPLICATION_SID = "BW_APPLICATION_SID"
BW_ACCOUNT_SID = "BW_ACCOUNT_SID"
BW_ACCOUNT_TOKEN = "BW_ACCOUNT_TOKEN"
BW_ACCOUNT_SECRET = "BW_ACCOUNT_SECRET"
BW_PHONE_NUMBER = "BW_PHONE_NUMBER"
BW_API_TYPE = "BW_API_TYPE"

BWI_USERNAME = "BWI_USERNAME"
BWI_PASSWORD = "BWI_PASSWORD"
BWI_ENCODING = "BWI_ENCODING"
BWI_SENDER = "BWI_SENDER"


class BandwidthOrgModelOverrides(Org):
    # fake model, tell Django to ignore so it does not try to create/migrate schema.
    class Meta:
        abstract = True
    override_ignore = ignoreDjangoModelAttrs(Org)

    def connect_bandwidth(self, account_sid, account_token, account_secret, application_sid, user):
        self.config.update({
            BW_ACCOUNT_SID: account_sid,
            BW_ACCOUNT_TOKEN: account_token,
            BW_ACCOUNT_SECRET: account_secret,
            BW_APPLICATION_SID: application_sid,
        })
        self.modified_by = user
        self.save(update_fields=("config", "modified_by", "modified_on"))

    def connect_bandwidth_international(self, username, password, user):
        """
        BWI Unsupported
        """
        pass

    def is_connected_to_bandwidth(self):
        if self.config:
            bw_account_sid = self.config.get(BW_ACCOUNT_SID, None)
            bw_account_token = self.config.get(BW_ACCOUNT_TOKEN, None)
            if bw_account_sid and bw_account_token:
                return True
        return False

    def is_connected_to_bandwidth_international(self):
        """
        BWI Unsupported
        """
        return False

    def get_bandwidth_messaging_client(self):
        if self.config:
            bw_account_sid = self.config.get(BW_ACCOUNT_SID, None)
            bw_account_token = self.config.get(BW_ACCOUNT_TOKEN, None)
            bw_account_secret = self.config.get(BW_ACCOUNT_SECRET, None)

            if bw_account_sid and bw_account_token and bw_account_secret:
                return bandwidth.client('messaging', bw_account_sid, bw_account_token, bw_account_secret)
        return None

    def get_bandwidth_international_messaging_client(self):
        """
        BWI Unsupported
        """
        return None

    def remove_bandwidth_account(self, user, international=False):
        if self.config:
            channel_type = "BWD"
            if international:
                channel_type = "BWI"

            for channel in self.channels.filter(is_active=True, channel_type__in=[channel_type]):
                channel.release()

            if channel_type == "BWI":
                self.config[BWI_USERNAME] = ""
                self.config[BWI_PASSWORD] = ""
            elif channel_type == "BWD":
                self.config[BW_ACCOUNT_SID] = ""
                self.config[BW_APPLICATION_SID] = ""
                self.config[BW_ACCOUNT_TOKEN] = ""
                self.config[BW_ACCOUNT_SECRET] = ""

            self.modified_by = user
            self.save()
    #enddef remove_bandwidth_account

#endclass BandwidthOrgModelOverrides
