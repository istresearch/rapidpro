import logging
import requests

from django.conf import settings

from celery import shared_task

from temba.channels.models import Channel
from temba.channels.types.postmaster import PostmasterType

logger = logging.getLogger(__name__)

@shared_task(track_started=True, name="update_postmaster_sync_task")
def update_postmaster_sync_task():
    """
    Run every 5 minutes and updates postmaster channel sync times.
    """
    api_url = getattr(settings, "POST_OFFICE_API_URL")
    api_key = getattr(settings, "POST_OFFICE_API_KEY")
    for channel in Channel.objects.filter(is_active=True, channel_type=PostmasterType.code):
        resp = None
        try:
            resp = requests.get(f"{api_url}/engage/admin/device?id={channel.address}", headers={'po-api-key': api_key})
            last_seen = resp.json()['devices'][0]['last_seen']
            if last_seen is not None:
                if channel.last_seen is None or channel.last_seen < last_seen:
                    channel.last_seen = last_seen
                    channel.save()
        except Exception as ex:
            logger.exception(f"{ex}", extra={
                'url': f"{api_url}/engage/admin/device?id={channel.address}",
                'channel_name': channel.name,
                'channel_addr': channel.address,
                'response_code': resp.status_code if resp else None,
                'response_body': resp.content if resp else None,
            })
