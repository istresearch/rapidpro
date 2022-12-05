import logging
import phonenumbers
import re

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.channels.models import Channel
from temba.channels.types.vonage.type import VonageType
from temba.channels.types.vonage.views import ClaimView


logger = logging.getLogger(__name__)

class ClaimViewOverrides(ClassOverrideMixinMustBeFirst, ClaimView):

    def get_existing_numbers(self, org):
        numbers = []
        client = org.get_vonage_client()
        if client:
            account_numbers = client.get_numbers(size=100)
            account_uuids = []
            for number in account_numbers:
                if number["type"] == "mobile-shortcode":  # pragma: needs cover
                    phone_number = number["msisdn"]
                else:
                    parsed = phonenumbers.parse(number["msisdn"], number["country"])
                    phone_number = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                #endif shortcode

                # mark accounts used/unused by checking the db for uuid
                # 'moHttpUrl': 'https://engage.dev.istresearch.com/c/nx/742c11f1-72fb-4994-8156-8848e8a63e55/receive',
                pattern = re.compile(r"(?<=c/nx/).{8}-.{4}-.{4}-.{4}-.{12}(?=/receive)")
                match = pattern.match(number["moHttpUrl"])
                channel_uuid = match.string if match else None
                account_uuids.append(channel_uuid)

                numbers.append(dict(
                    number=phone_number,
                    country=number["country"],
                    uuid=channel_uuid,
                    in_use=False,
                ))
            #endfor numbers

            # query db for "in use" numbers
            qs = Channel.objects.filter(
                channel_type=VonageType.code,
                uuid__in=account_uuids,
            )
            for channel in qs:
                idx = account_uuids.index(channel.uuid)
                account_numbers[idx].in_use = True
            #endfor each channel found
            logger.debug(' TRACE='+str(account_numbers))

        #endif client
        return numbers
