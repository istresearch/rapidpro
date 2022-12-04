import logging

from django.urls import reverse

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.channels.types.vonage.client import VonageClient


logger = logging.getLogger(__name__)

class VonageClientOverrides(ClassOverrideMixinMustBeFirst, VonageClient):

    def create_application(self, domain, channel_uuid):
        """
        Vonage got bought out and changed their API.
        :param domain:
        :param channel_uuid:
        :return:
        """
        name = "%s/%s" % (domain, channel_uuid)
        inbound_url = reverse("mailroom.ivr_handler", args=[channel_uuid, "incoming"])
        status_url = reverse("mailroom.ivr_handler", args=[channel_uuid, "status"])
        response = self.base.application_v2.create_application({
            "name": f"{name}",
            "capabilities": {
                "messages": {
                    "webhooks": {
                        "inbound_url": {
                            "address": f"https://{domain}{inbound_url}",
                            "http_method": "POST"
                        },
                        "status_url": {
                            "address": f"https://{domain}{status_url}",
                            "http_method": "POST"
                        }
                    }
                },
                "voice": {
                    "webhooks": {
                        "answer_url": {
                            "address": f"https://{domain}{inbound_url}",
                            "http_method": "POST"
                        },
                        "event_url": {
                            "address": f"https://{domain}{status_url}",
                            "http_method": "POST"
                        }
                    }
                }
            }
        })

        app_id = response.get("id")
        app_private_key = response.get("keys", {}).get("private_key")
        return app_id, app_private_key
    #enddef create_application

    def get_numbers(self, pattern: str = None, size: int = 10) -> list:
        params = {"size": size}
        if pattern:
            params["pattern"] = str(pattern).strip("+")

        response = self._with_retry(self.base.get_account_numbers, params=params)
        logger.debug(' TRACE[get_numbers]', {response})
        return response["numbers"] if int(response.get("count", 0)) else []
    #enddef get_numbers

#endclass VonageClientOverrides
