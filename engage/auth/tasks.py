import logging

from celery.task import task


logger = logging.getLogger(__name__)

@task(track_started=True, name="clear_stale_auth_tokens")
def clear_stale_auth_tokens():  # pragma: needs cover
    from oauth2_provider.models import clear_expired
    clear_expired()
    logger.info("cleared stale auth tokens")
