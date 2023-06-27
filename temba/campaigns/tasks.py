import logging

from django.conf import settings
from django.utils import timezone
from django.utils.timesince import timesince

from temba.campaigns.models import EventFire
from temba.utils import chunk_list
from temba.utils.celery import nonoverlapping_task

logger = logging.getLogger(__name__)

EVENT_FIRES_TO_TRIM = 100_000


@nonoverlapping_task(track_started=True, name="trim_event_fires_task")
def trim_event_fires_task():
    trim_before = timezone.now() - settings.RETENTION_PERIODS["eventfire"]
    start = timezone.now()

    # first look for unfired fires that belong to inactive events
    trim_ids = list(
        EventFire.objects.filter(fired=None, event__is_active=False).values_list("id", flat=True)[:EVENT_FIRES_TO_TRIM]
    )

    # if we have trimmed all of our unfired inactive fires, look for old fired ones
    if len(trim_ids) < EVENT_FIRES_TO_TRIM:
        trim_ids += list(
            EventFire.objects.filter(fired__lt=trim_before)
            .values_list("id", flat=True)
            .order_by("fired")[: EVENT_FIRES_TO_TRIM - len(trim_ids)]
        )

    for batch in chunk_list(trim_ids, 100):
        # use a bulk delete for performance reasons, nothing references EventFire
        EventFire.objects.filter(id__in=batch).delete()

    logger.info(f"Deleted {len(trim_ids)} event fires in {timesince(start)}")
