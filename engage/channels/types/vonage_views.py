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
            try:
                account_numbers = client.get_numbers(size=100)
                #logger.debug(' TRACE[account_numbers]='+str(account_numbers))
                uuid_pattern = r"(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})/receive$"
                account_uuids = []
                for number in account_numbers:
                    if number["type"] == "mobile-shortcode":  # pragma: needs cover
                        phone_number = number["msisdn"]
                    else:
                        parsed = phonenumbers.parse(number["msisdn"], number["country"])
                        phone_number = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                    #endif shortcode

                    # mark accounts used/unused by checking the db for uuid
                    channel_uuid = '1'
                    if 'moHttpUrl' in number:
                        # 'moHttpUrl': 'https://engage.dev.istresearch.com/c/nx/742c11f1-72fb-4994-8156-8848e8a63e55/receive',
                        match = re.search(uuid_pattern, number["moHttpUrl"])
                        channel_uuid = match.group(1) if match else '1'
                    #endif key in list
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
                ).values_list('uuid', flat=True)
                for channel_uuid in qs:
                    idx = account_uuids.index(channel_uuid)
                    numbers[idx]['in_use'] = True
                #endfor each channel found
                #logger.debug(' TRACE[nums]='+str(numbers))
            except Exception as e:
                logger.error(f"fail: {str(e)}", exc_info=True)
                raise e
            #endtry

        #endif client
        return numbers
    #enddef get_existing_numbers

#endclass ClaimViewOverrides
